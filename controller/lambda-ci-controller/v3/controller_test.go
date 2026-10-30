package main

import (
	"context"
	"log/slog"
	"os"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/actions/scaleset"
)

func testPolicy() controllerPolicy {
	return controllerPolicy{
		SchemaVersion:                1,
		RunnerClassID:                "workspace-control-control-small-v1",
		Repository:                   "adamtrott78/workspace-control",
		ScaleSetName:                 "lambda-v3-wc-control",
		RunnerPrefix:                 "lambda-v3-wc-control-",
		MaxRunners:                   1,
		ControlPlaneGenerationSHA256: strings.Repeat("a", 64),
		ControllerPolicySHA256:       strings.Repeat("b", 64),
		TrustedWorkflows: []trustedWorkflow{{
			RouteID:                     "control",
			Path:                        ".github/workflows/control.yml",
			DefaultBranch:               "main",
			BlobSHA:                     strings.Repeat("c", 40),
			CompileTimeJobKey:           "control",
			CompileTimeTopLevelJobCount: 1,
			AllowedEvents:               []string{"issue_comment"},
			AllowedActorLogins:          []string{"adamtrott78"},
		}},
	}
}

type memoryLedger struct {
	mu      sync.Mutex
	records map[int64]jobRecord
}

func newMemoryLedger() *memoryLedger {
	return &memoryLedger{records: map[int64]jobRecord{}}
}

func (m *memoryLedger) List() ([]jobRecord, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := make([]jobRecord, 0, len(m.records))
	for _, record := range m.records {
		out = append(out, record)
	}
	return out, nil
}

func (m *memoryLedger) Get(id int64) (jobRecord, bool, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	record, ok := m.records[id]
	return record, ok, nil
}

func (m *memoryLedger) Put(record jobRecord) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.records[record.RunnerRequestID] = record
	return nil
}

type fakeVerifier struct {
	trusted bool
	reason  string
	err     error
}

func (f *fakeVerifier) Verify(
	_ context.Context,
	job *scaleset.JobMessageBase,
) (verifiedJob, bool, string, error) {
	if f.err != nil {
		return verifiedJob{}, false, "", f.err
	}
	if !f.trusted {
		return verifiedJob{}, false, f.reason, nil
	}
	return verifiedJob{
		RunnerRequestID:      job.RunnerRequestID,
		WorkflowRunID:        job.WorkflowRunID,
		WorkflowPath:         ".github/workflows/control.yml",
		WorkflowBlobSHA:      strings.Repeat("c", 40),
		ActorLogin:           "adamtrott78",
		TriggeringActorLogin: "adamtrott78",
		EventName:            "issue_comment",
	}, true, "", nil
}

type fakeSession struct {
	acquireCalls [][]int64
}

func (f *fakeSession) AcquireJobs(
	_ context.Context,
	ids []int64,
) ([]int64, error) {
	copyIDs := append([]int64(nil), ids...)
	f.acquireCalls = append(f.acquireCalls, copyIDs)
	return copyIDs, nil
}

type fakeJIT struct {
	events      *[]string
	nextID      int
	removeCalls []int64
}

func (f *fakeJIT) GenerateJitRunnerConfig(
	_ context.Context,
	settings *scaleset.RunnerScaleSetJitRunnerSetting,
	_ int,
) (*scaleset.RunnerScaleSetJitRunnerConfig, error) {
	*f.events = append(*f.events, "jit:"+settings.Name)
	f.nextID++
	return &scaleset.RunnerScaleSetJitRunnerConfig{
		Runner: &scaleset.RunnerReference{
			ID:   f.nextID,
			Name: settings.Name,
		},
		EncodedJITConfig: "encoded-jit",
	}, nil
}

func (f *fakeJIT) RemoveRunner(_ context.Context, id int64) error {
	f.removeCalls = append(f.removeCalls, id)
	*f.events = append(*f.events, "remove")
	return nil
}

type fakeRoot struct {
	events          *[]string
	reserveStatus   string
	statusByRequest map[string]string
	reserveIDs      []string
	launchIDs       []string
}

func newFakeRoot(events *[]string) *fakeRoot {
	return &fakeRoot{
		events:          events,
		statusByRequest: map[string]string{},
	}
}

func (f *fakeRoot) Reserve(
	_ context.Context,
	requestID string,
	runnerName string,
) (capacityResponse, error) {
	*f.events = append(*f.events, "reserve:"+runnerName)
	f.reserveIDs = append(f.reserveIDs, requestID)
	status := f.reserveStatus
	if status == "" {
		status = "RESERVED"
	}
	if status == "RESERVED" {
		f.statusByRequest[requestID] = "RESERVED"
	}
	return capacityResponse{
		SchemaVersion: 3,
		Operation:     "RESERVE_RESULT",
		Status:        status,
		RequestID:     requestID,
	}, nil
}

func (f *fakeRoot) Launch(
	_ context.Context,
	requestID string,
	runnerName string,
	_ string,
) (capacityResponse, error) {
	*f.events = append(*f.events, "launch:"+runnerName)
	f.launchIDs = append(f.launchIDs, requestID)
	f.statusByRequest[requestID] = "PREPARING"
	return capacityResponse{
		SchemaVersion: 3,
		Operation:     "LAUNCH_RESULT",
		Status:        "PREPARING",
		RequestID:     requestID,
	}, nil
}

func (f *fakeRoot) Status(
	_ context.Context,
	requestID string,
) (capacityResponse, error) {
	status := f.statusByRequest[requestID]
	if status == "" {
		status = "MISSING"
	}
	return capacityResponse{
		SchemaVersion: 3,
		Operation:     "STATUS_RESULT",
		Status:        status,
		RequestID:     requestID,
	}, nil
}

func (f *fakeRoot) Cancel(
	_ context.Context,
	requestID string,
) (capacityResponse, error) {
	status := f.statusByRequest[requestID]
	if status == "RESERVED" {
		f.statusByRequest[requestID] = "CANCELED"
		return capacityResponse{
			SchemaVersion: 3,
			Operation:     "CANCEL_RESULT",
			Status:        "CANCELED",
			RequestID:     requestID,
		}, nil
	}
	return capacityResponse{
		SchemaVersion: 3,
		Operation:     "CANCEL_RESULT",
		Status:        "NOT_CANCELABLE",
		RequestID:     requestID,
	}, nil
}

func testScaler(
	verifier jobVerifier,
	ledger ledgerStore,
	session jobAcquirer,
	jit runnerJITClient,
	root capacityClient,
) *v3Scaler {
	return &v3Scaler{
		policy:     testPolicy(),
		verifier:   verifier,
		ledger:     ledger,
		session:    session,
		jit:        jit,
		root:       root,
		scaleSetID: 7,
		logger:     slog.New(slog.DiscardHandler),
		now:        func() time.Time { return time.Date(2026, 10, 30, 0, 0, 0, 0, time.UTC) },
	}
}

func available(id, runID int64) *scaleset.JobAvailable {
	return &scaleset.JobAvailable{
		JobMessageBase: scaleset.JobMessageBase{
			JobMessageType: scaleset.JobMessageType{
				MessageType: scaleset.MessageTypeJobAvailable,
			},
			RunnerRequestID: id,
			OwnerName:       "adamtrott78",
			RepositoryName:  "workspace-control",
			WorkflowRunID:   runID,
			EventName:       "issue_comment",
			JobWorkflowRef:  "adamtrott78/workspace-control/.github/workflows/control.yml@refs/heads/main",
			RequestLabels:   []string{"lambda-v3-wc-control"},
			JobDisplayName:  "attacker-controlled text that must carry no authority",
		},
	}
}

func assigned(id, runID int64) *scaleset.JobAssigned {
	return &scaleset.JobAssigned{
		JobMessageBase: scaleset.JobMessageBase{
			JobMessageType: scaleset.JobMessageType{
				MessageType: scaleset.MessageTypeJobAssigned,
			},
			RunnerRequestID: id,
			OwnerName:       "adamtrott78",
			RepositoryName:  "workspace-control",
			WorkflowRunID:   runID,
			EventName:       "issue_comment",
			JobWorkflowRef:  "adamtrott78/workspace-control/.github/workflows/control.yml@refs/heads/main",
			RequestLabels:   []string{"lambda-v3-wc-control"},
		},
	}
}

func TestProductionV3SourceDoesNotReadDisplayOrCandidateAuthority(t *testing.T) {
	for _, path := range []string{"controller.go", "main.go"} {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		source := string(raw)
		for _, forbidden := range []string{
			".JobDisplayName",
			"PRNumber",
			"CandidateSHA",
			"workloadForDisplayClaim",
		} {
			if strings.Contains(source, forbidden) {
				t.Fatalf("%s contains forbidden authority parser token %q", path, forbidden)
			}
		}
	}
}

func TestTrustedAvailableIsAcquiredBeforeCapacityButNotProvisionedUntilAssignedCount(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	session := &fakeSession{}
	jit := &fakeJIT{events: &events}
	root := newFakeRoot(&events)
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		session,
		jit,
		root,
	)

	err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		JobAvailableMessages: []*scaleset.JobAvailable{available(11, 101)},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(session.acquireCalls) != 1 || len(session.acquireCalls[0]) != 1 || session.acquireCalls[0][0] != 11 {
		t.Fatalf("trusted scheduler job not acquired exactly once: %#v", session.acquireCalls)
	}
	if len(events) != 0 {
		t.Fatalf("capacity provisioned before TotalAssignedJobs authority: %#v", events)
	}

	err = scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 3 {
		t.Fatalf("unexpected provision sequence: %#v", events)
	}
	if !strings.HasPrefix(events[0], "reserve:") ||
		!strings.HasPrefix(events[1], "jit:") ||
		!strings.HasPrefix(events[2], "launch:") {
		t.Fatalf("must preserve RESERVE -> JIT -> LAUNCH, got %#v", events)
	}
}

func TestAnomalousAvailableIsAckLocalWithoutAcquireOrProvision(t *testing.T) {
	events := []string{}
	session := &fakeSession{}
	scaler := testScaler(
		&fakeVerifier{trusted: false, reason: "workflow blob mismatch"},
		newMemoryLedger(),
		session,
		&fakeJIT{events: &events},
		newFakeRoot(&events),
	)
	err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
		JobAvailableMessages: []*scaleset.JobAvailable{available(12, 102)},
	})
	if err != nil {
		t.Fatal(err)
	}
	if len(session.acquireCalls) != 0 || len(events) != 0 {
		t.Fatalf("untrusted work reached scheduler/root authority")
	}
}

func TestBusyIsCapacityLocalAndNeverGeneratesJIT(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	session := &fakeSession{}
	root := newFakeRoot(&events)
	root.reserveStatus = "BUSY"
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		session,
		&fakeJIT{events: &events},
		root,
	)
	if err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		JobAvailableMessages: []*scaleset.JobAvailable{available(13, 103)},
	}); err != nil {
		t.Fatal(err)
	}
	if err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	}); err != nil {
		t.Fatal(err)
	}
	if len(events) != 1 || !strings.HasPrefix(events[0], "reserve:") {
		t.Fatalf("BUSY must stop before JIT: %#v", events)
	}
	record, ok, _ := ledger.Get(13)
	if !ok || record.State != "WAITING_CAPACITY" {
		t.Fatalf("BUSY must remain request-local waiting state: %#v", record)
	}
}

func TestAssignedMessageCanReconstructTrustedSchedulerAuthority(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		&fakeSession{},
		&fakeJIT{events: &events},
		newFakeRoot(&events),
	)
	if err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics:          &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
		JobAssignedMessages: []*scaleset.JobAssigned{assigned(14, 104)},
	}); err != nil {
		t.Fatal(err)
	}
	record, ok, _ := ledger.Get(14)
	if !ok {
		t.Fatal("assigned structured identity did not reconstruct ledger")
	}
	if record.SchedulerState != "ASSIGNED" || record.State != "PREPARING" {
		t.Fatalf("unexpected reconstructed/provisioned state: %#v", record)
	}
	if len(events) != 3 {
		t.Fatalf("reconstructed assigned work did not follow full capacity sequence: %#v", events)
	}
}

func TestAvailableRedeliveryDoesNotAcquireOrProvisionTwice(t *testing.T) {
	events := []string{}
	session := &fakeSession{}
	ledger := newMemoryLedger()
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		session,
		&fakeJIT{events: &events},
		newFakeRoot(&events),
	)
	msg := &scaleset.RunnerScaleSetMessage{
		Statistics:           &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 0},
		JobAvailableMessages: []*scaleset.JobAvailable{available(15, 105)},
	}
	if err := scaler.Scale(context.Background(), msg); err != nil {
		t.Fatal(err)
	}
	if err := scaler.Scale(context.Background(), msg); err != nil {
		t.Fatal(err)
	}
	if len(session.acquireCalls) != 1 {
		t.Fatalf("redelivery reacquired trusted job: %#v", session.acquireCalls)
	}
	if len(events) != 0 {
		t.Fatalf("redelivery invented capacity without assigned count: %#v", events)
	}
}

func TestCrashAfterJITBeforeLaunchRemovesOrphanThenRegenerates(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	jit := &fakeJIT{events: &events}
	root := newFakeRoot(&events)
	policy := testPolicy()
	job := verifiedJob{
		RunnerRequestID: 16,
		WorkflowRunID:   106,
		WorkflowPath:    ".github/workflows/control.yml",
		WorkflowBlobSHA: strings.Repeat("c", 40),
	}
	record, err := newJobRecord(policy, job, "JIT_REGISTERED", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	record.JITRunnerID = 99
	record.JITSHA256 = strings.Repeat("d", 64)
	root.statusByRequest[record.RequestID] = "RESERVED"
	if err := ledger.Put(record); err != nil {
		t.Fatal(err)
	}
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		&fakeSession{},
		jit,
		root,
	)
	if err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	}); err != nil {
		t.Fatal(err)
	}
	if len(jit.removeCalls) != 1 || jit.removeCalls[0] != 99 {
		t.Fatalf("orphan JIT not removed exactly: %#v", jit.removeCalls)
	}
	if len(events) < 3 || events[0] != "remove" || !strings.HasPrefix(events[1], "jit:") || !strings.HasPrefix(events[2], "launch:") {
		t.Fatalf("unexpected recovery sequence: %#v", events)
	}
}

func TestCanceledReservationUsesFreshProvisionIdentity(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	root := newFakeRoot(&events)
	policy := testPolicy()
	job := verifiedJob{
		RunnerRequestID: 17,
		WorkflowRunID:   107,
		WorkflowPath:    ".github/workflows/control.yml",
		WorkflowBlobSHA: strings.Repeat("c", 40),
	}
	record, err := newJobRecord(policy, job, "RESERVED", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	oldRequestID := record.RequestID
	root.statusByRequest[oldRequestID] = "CANCELED"
	if err := ledger.Put(record); err != nil {
		t.Fatal(err)
	}
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		&fakeSession{},
		&fakeJIT{events: &events},
		root,
	)
	if err := scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	}); err != nil {
		t.Fatal(err)
	}
	current, _, _ := ledger.Get(17)
	if current.ProvisionAttempt != 1 || current.RequestID == oldRequestID {
		t.Fatalf("expired/canceled root reservation did not mint fresh identity: %#v", current)
	}
	if len(root.reserveIDs) != 1 || root.reserveIDs[0] != current.RequestID {
		t.Fatalf("fresh request identity was not reserved: %#v", root.reserveIDs)
	}
}

func TestControllerPolicyDigestDriftIsFatalBeforeMutation(t *testing.T) {
	events := []string{}
	ledger := newMemoryLedger()
	policy := testPolicy()
	job := verifiedJob{
		RunnerRequestID: 18,
		WorkflowRunID:   108,
		WorkflowPath:    ".github/workflows/control.yml",
		WorkflowBlobSHA: strings.Repeat("c", 40),
	}
	record, err := newJobRecord(policy, job, "ACQUIRED", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	record.ControllerPolicySHA256 = strings.Repeat("e", 64)
	if err := ledger.Put(record); err != nil {
		t.Fatal(err)
	}
	scaler := testScaler(
		&fakeVerifier{trusted: true},
		ledger,
		&fakeSession{},
		&fakeJIT{events: &events},
		newFakeRoot(&events),
	)
	err = scaler.Scale(context.Background(), &scaleset.RunnerScaleSetMessage{
		Statistics: &scaleset.RunnerScaleSetStatistic{TotalAssignedJobs: 1},
	})
	if err == nil || !strings.Contains(err.Error(), "controller-policy binding mismatch") {
		t.Fatalf("policy drift must be fatal, got %v", err)
	}
	if len(events) != 0 {
		t.Fatalf("policy drift mutated capacity: %#v", events)
	}
}
