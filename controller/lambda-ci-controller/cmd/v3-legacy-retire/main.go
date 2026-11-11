package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"syscall"
	"time"

	"github.com/actions/scaleset"
	"github.com/google/uuid"
)

const (
	mode                    = "V3_LEGACY_SCALE_SET_RETIREMENT"
	productionMode          = "V3_PRODUCTION_GENERATION_CUTOVER"
	productionCommitted     = "COMMITTED_V3_PRODUCTION"
	receiptRoot             = "/var/lib/workspace-ci/v3/legacy-retirement"
	runnerGroupID           = 1
	rollbackWindowPhase     = "ROLLBACK_WINDOW_RECORDED"
	partialRetirementPhase  = "PARTIAL_RETIREMENT"
	completedPhase          = "COMPLETED_ACCEPTED_LEGACY_SCALE_SET_RETIREMENT"
)

var acceptedClasses = []string{
	"workspace-control-control-small-v1",
	"padataset-cpu-public-v1",
	"padataset-gpu-single-public-v1",
}

type retirementTarget struct {
	RepositoryURL string
	LegacyName    string
	TargetName    string
	RunnerClassID string
}

var retirementTargets = []retirementTarget{
	{
		RepositoryURL: "https://github.com/adamtrott78/workspace-control",
		LegacyName:    "lambda-workspace-control",
		TargetName:    "lambda-workspace-control-control-small",
		RunnerClassID: "workspace-control-control-small-v1",
	},
	{
		RepositoryURL: "https://github.com/adamtrott78/PADataset",
		LegacyName:    "lambda-padataset",
		TargetName:    "lambda-padataset-cpu-public",
		RunnerClassID: "padataset-cpu-public-v1",
	},
	{
		RepositoryURL: "https://github.com/adamtrott78/PADataset",
		LegacyName:    "lambda-padataset-gpu",
		TargetName:    "lambda-padataset-gpu-single-public",
		RunnerClassID: "padataset-gpu-single-public-v1",
	},
}

var preservedUnacceptedLegacyScaleSets = []string{
	"lambda-research-engine",
	"lambda-research-engine-gpu",
}

var acceptedV3Units = []string{
	"workspace-ci-v3-controller@workspace-control-control-small-v1.service",
	"workspace-ci-v3-controller@padataset-cpu-public-v1.service",
	"workspace-ci-v3-controller@padataset-gpu-single-public-v1.service",
}

var inactiveV3Units = []string{
	"workspace-ci-v3-controller@research-cpu-public-v1.service",
	"workspace-ci-v3-controller@research-gpu-single-public-v1.service",
	"workspace-ci-v3-controller@research-gpu-single-runtime-v1.service",
	"workspace-ci-v3-controller@research-model-single-offline-v1.service",
	"workspace-ci-v3-controller@research-model-dual-offline-v1.service",
	"workspace-ci-v3-controller@research-model-dual-public-v1.service",
}

var legacyV2Units = []string{
	"workspace-ci-controller@workspace-control-cpu.service",
	"workspace-ci-controller@padataset-cpu.service",
	"workspace-ci-controller@padataset-gpu.service",
	"workspace-ci-controller@research-engine-cpu.service",
	"workspace-ci-controller@research-engine-gpu.service",
}

var rootUnits = []string{
	"workspace-ci-v3-reconciler.service",
	"workspace-ci-v3-provisioner.service",
}

type productionReceipt struct {
	SchemaVersion                 int                        `json:"schema_version"`
	Mode                          string                     `json:"mode"`
	Phase                         string                     `json:"phase"`
	SourceHead                    string                     `json:"source_head"`
	ProductionGenerationSHA256    string                     `json:"production_generation_sha256"`
	AcceptedRunnerClassIDs        []string                   `json:"accepted_runner_class_ids"`
	WorkflowBindings              map[string]json.RawMessage `json:"workflow_bindings"`
	ProductionValidationConfirmed bool                       `json:"production_validation_confirmed"`
}

type scaleSetSnapshot struct {
	RepositoryURL          string `json:"repository_url"`
	LegacyName             string `json:"legacy_name"`
	LegacyID               int    `json:"legacy_id"`
	TargetName             string `json:"target_name"`
	TargetID               int    `json:"target_id"`
	RunnerClassID          string `json:"runner_class_id"`
	TotalAvailableJobs     int    `json:"total_available_jobs"`
	TotalAcquiredJobs      int    `json:"total_acquired_jobs"`
	TotalAssignedJobs      int    `json:"total_assigned_jobs"`
	TotalRunningJobs       int    `json:"total_running_jobs"`
	TotalRegisteredRunners int    `json:"total_registered_runners"`
	TotalBusyRunners       int    `json:"total_busy_runners"`
	Retired                bool   `json:"retired"`
	RetiredAtUTC           string `json:"retired_at_utc,omitempty"`
}

type retirementReceipt struct {
	SchemaVersion                  int                `json:"schema_version"`
	Mode                           string             `json:"mode"`
	ReceiptID                      string             `json:"receipt_id"`
	SourceHead                     string             `json:"source_head"`
	ProductionTransaction          string             `json:"production_transaction"`
	ProductionTransactionSHA256    string             `json:"production_transaction_sha256"`
	ProductionSourceHead           string             `json:"production_source_head"`
	ProductionGenerationSHA256     string             `json:"production_generation_sha256"`
	AcceptedRunnerClassIDs         []string           `json:"accepted_runner_class_ids"`
	PreservedLegacyBytesConfigState bool              `json:"preserved_legacy_bytes_config_state"`
	PreservedUnacceptedScaleSets   []string           `json:"preserved_unaccepted_legacy_scale_sets"`
	RollbackWindowRecordedAtUTC    string             `json:"rollback_window_recorded_at_utc"`
	Targets                        []scaleSetSnapshot `json:"targets"`
	Phase                          string             `json:"phase"`
	LastError                      string             `json:"last_error,omitempty"`
	CompletedAtUTC                 string             `json:"completed_at_utc,omitempty"`
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}

func canonicalJSON(v any) []byte {
	raw, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		panic(err)
	}
	return append(raw, '\n')
}

func sha256Bytes(raw []byte) string {
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func readJSON(path string, out any) ([]byte, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(raw, out); err != nil {
		return nil, err
	}
	return raw, nil
}

func ensureRootPrivateDir(path string) error {
	if os.Geteuid() != 0 {
		return errors.New("must run as root")
	}
	if err := os.MkdirAll(path, 0o700); err != nil {
		return err
	}
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	st, ok := info.Sys().(*syscall.Stat_t)
	if !ok {
		return errors.New("cannot inspect receipt root ownership")
	}
	if st.Uid != 0 || st.Gid != 0 || info.Mode().Perm() != 0o700 {
		return fmt.Errorf("receipt root ownership/mode drift uid=%d gid=%d mode=%o", st.Uid, st.Gid, info.Mode().Perm())
	}
	return nil
}

func atomicWriteReceipt(path string, receipt *retirementReceipt) error {
	dir := filepath.Dir(path)
	if err := ensureRootPrivateDir(dir); err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, ".receipt-*.tmp")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer os.Remove(tmpName)
	if err := tmp.Chmod(0o600); err != nil {
		tmp.Close()
		return err
	}
	raw := canonicalJSON(receipt)
	if _, err := tmp.Write(raw); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Rename(tmpName, path); err != nil {
		return err
	}
	return nil
}

func systemctlState(unit string, property string) (bool, error) {
	var argv []string
	switch property {
	case "active":
		argv = []string{"is-active", "--quiet", unit}
	case "enabled":
		argv = []string{"is-enabled", "--quiet", unit}
	default:
		return false, fmt.Errorf("unknown systemctl property %q", property)
	}
	cmd := exec.Command("systemctl", argv...)
	err := cmd.Run()
	if err == nil {
		return true, nil
	}
	var exitErr *exec.ExitError
	if errors.As(err, &exitErr) {
		return false, nil
	}
	return false, err
}

func requireSystemdPostCommit() error {
	for _, unit := range rootUnits {
		active, err := systemctlState(unit, "active")
		if err != nil || !active {
			return fmt.Errorf("root unit is not active: %s", unit)
		}
		enabled, err := systemctlState(unit, "enabled")
		if err != nil || !enabled {
			return fmt.Errorf("root unit is not enabled: %s", unit)
		}
	}
	for _, unit := range acceptedV3Units {
		active, err := systemctlState(unit, "active")
		if err != nil || !active {
			return fmt.Errorf("accepted v3 unit is not active: %s", unit)
		}
		enabled, err := systemctlState(unit, "enabled")
		if err != nil || !enabled {
			return fmt.Errorf("accepted v3 unit is not enabled: %s", unit)
		}
	}
	for _, unit := range inactiveV3Units {
		active, err := systemctlState(unit, "active")
		if err != nil || active {
			return fmt.Errorf("unaccepted v3 unit is active: %s", unit)
		}
		enabled, err := systemctlState(unit, "enabled")
		if err != nil || enabled {
			return fmt.Errorf("unaccepted v3 unit is enabled: %s", unit)
		}
	}
	for _, unit := range legacyV2Units {
		active, err := systemctlState(unit, "active")
		if err != nil || active {
			return fmt.Errorf("legacy v2 unit is active: %s", unit)
		}
		enabled, err := systemctlState(unit, "enabled")
		if err != nil || enabled {
			return fmt.Errorf("legacy v2 unit is enabled: %s", unit)
		}
	}
	return nil
}

func validateProductionReceipt(path string) (*productionReceipt, []byte, error) {
	var receipt productionReceipt
	raw, err := readJSON(path, &receipt)
	if err != nil {
		return nil, nil, fmt.Errorf("read production transaction: %w", err)
	}
	if receipt.SchemaVersion != 1 || receipt.Mode != productionMode {
		return nil, nil, errors.New("production transaction mode/schema mismatch")
	}
	if receipt.Phase != productionCommitted {
		return nil, nil, fmt.Errorf("production transaction is not committed: %s", receipt.Phase)
	}
	if !receipt.ProductionValidationConfirmed {
		return nil, nil, errors.New("production validation is not confirmed")
	}
	if !reflect.DeepEqual(receipt.AcceptedRunnerClassIDs, acceptedClasses) {
		return nil, nil, fmt.Errorf("accepted class set mismatch: %v", receipt.AcceptedRunnerClassIDs)
	}
	if len(receipt.WorkflowBindings) != len(retirementTargets) {
		return nil, nil, errors.New("production workflow binding count mismatch")
	}
	return &receipt, raw, nil
}

func clientFor(url, token, sourceHead string) (*scaleset.Client, error) {
	return scaleset.NewClientWithPersonalAccessToken(
		scaleset.NewClientWithPersonalAccessTokenConfig{
			GitHubConfigURL:     url,
			PersonalAccessToken: token,
			SystemInfo: scaleset.SystemInfo{
				System:    "workspace-control",
				Version:   "v3",
				CommitSHA: sourceHead,
				Subsystem: "lambda-ci-v3-legacy-retirement",
			},
		},
	)
}

func requireDrained(name string, ss *scaleset.RunnerScaleSet) error {
	if ss == nil {
		return fmt.Errorf("legacy scale set is missing before retirement: %s", name)
	}
	if ss.ID <= 0 || ss.Name != name || ss.RunnerGroupID != runnerGroupID {
		return fmt.Errorf("legacy scale-set identity mismatch for %s", name)
	}
	if ss.Statistics == nil {
		return fmt.Errorf("legacy scale set lacks statistics: %s", name)
	}
	st := ss.Statistics
	if st.TotalAvailableJobs != 0 ||
		st.TotalAcquiredJobs != 0 ||
		st.TotalAssignedJobs != 0 ||
		st.TotalRunningJobs != 0 ||
		st.TotalRegisteredRunners != 0 ||
		st.TotalBusyRunners != 0 {
		return fmt.Errorf(
			"legacy scale set %s not drained available=%d acquired=%d assigned=%d running=%d registered=%d busy=%d",
			name,
			st.TotalAvailableJobs,
			st.TotalAcquiredJobs,
			st.TotalAssignedJobs,
			st.TotalRunningJobs,
			st.TotalRegisteredRunners,
			st.TotalBusyRunners,
		)
	}
	return nil
}

func snapshotTarget(ctx context.Context, token, sourceHead string, target retirementTarget) (scaleSetSnapshot, error) {
	client, err := clientFor(target.RepositoryURL, token, sourceHead)
	if err != nil {
		return scaleSetSnapshot{}, err
	}
	legacy, err := client.GetRunnerScaleSet(ctx, runnerGroupID, target.LegacyName)
	if err != nil {
		return scaleSetSnapshot{}, fmt.Errorf("get legacy scale set %s: %w", target.LegacyName, err)
	}
	if err := requireDrained(target.LegacyName, legacy); err != nil {
		return scaleSetSnapshot{}, err
	}
	v3, err := client.GetRunnerScaleSet(ctx, runnerGroupID, target.TargetName)
	if err != nil {
		return scaleSetSnapshot{}, fmt.Errorf("get target scale set %s: %w", target.TargetName, err)
	}
	if v3 == nil || v3.ID <= 0 || v3.Name != target.TargetName || v3.RunnerGroupID != runnerGroupID {
		return scaleSetSnapshot{}, fmt.Errorf("accepted target scale set missing or mismatched: %s", target.TargetName)
	}
	st := legacy.Statistics
	return scaleSetSnapshot{
		RepositoryURL:          target.RepositoryURL,
		LegacyName:             target.LegacyName,
		LegacyID:               legacy.ID,
		TargetName:             target.TargetName,
		TargetID:               v3.ID,
		RunnerClassID:          target.RunnerClassID,
		TotalAvailableJobs:     st.TotalAvailableJobs,
		TotalAcquiredJobs:      st.TotalAcquiredJobs,
		TotalAssignedJobs:      st.TotalAssignedJobs,
		TotalRunningJobs:       st.TotalRunningJobs,
		TotalRegisteredRunners: st.TotalRegisteredRunners,
		TotalBusyRunners:       st.TotalBusyRunners,
	}, nil
}

func verifySnapshotStillDrained(ctx context.Context, client *scaleset.Client, snap scaleSetSnapshot) (*scaleset.RunnerScaleSet, error) {
	ss, err := client.GetRunnerScaleSet(ctx, runnerGroupID, snap.LegacyName)
	if err != nil {
		return nil, err
	}
	if err := requireDrained(snap.LegacyName, ss); err != nil {
		return nil, err
	}
	if ss.ID != snap.LegacyID {
		return nil, fmt.Errorf("legacy scale-set ID changed for %s: got=%d expected=%d", snap.LegacyName, ss.ID, snap.LegacyID)
	}
	return ss, nil
}

func loadResumeReceipt(path string, sourceHead, productionTransaction string) (*retirementReceipt, error) {
	var receipt retirementReceipt
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}
	st, ok := info.Sys().(*syscall.Stat_t)
	if !ok || st.Uid != 0 || st.Gid != 0 || info.Mode().Perm() != 0o600 {
		return nil, errors.New("resume receipt ownership/mode invalid")
	}
	if err := json.Unmarshal(raw, &receipt); err != nil {
		return nil, err
	}
	if receipt.SchemaVersion != 1 || receipt.Mode != mode {
		return nil, errors.New("resume receipt mode/schema mismatch")
	}
	if receipt.SourceHead != sourceHead || receipt.ProductionTransaction != productionTransaction {
		return nil, errors.New("resume receipt binding mismatch")
	}
	if receipt.Phase != rollbackWindowPhase && receipt.Phase != partialRetirementPhase {
		return nil, fmt.Errorf("resume receipt is not resumable: %s", receipt.Phase)
	}
	return &receipt, nil
}

func applyRetirement(ctx context.Context, token, sourceHead, productionTransaction, resumePath string) (string, error) {
	if os.Geteuid() != 0 {
		return "", errors.New("legacy scale-set retirement must run as root")
	}
	production, productionRaw, err := validateProductionReceipt(productionTransaction)
	if err != nil {
		return "", err
	}
	if err := requireSystemdPostCommit(); err != nil {
		return "", err
	}

	var receipt *retirementReceipt
	var receiptPath string
	if resumePath != "" {
		receipt, err = loadResumeReceipt(resumePath, sourceHead, productionTransaction)
		if err != nil {
			return "", err
		}
		if receipt.ProductionTransactionSHA256 != sha256Bytes(productionRaw) ||
			receipt.ProductionGenerationSHA256 != production.ProductionGenerationSHA256 ||
			receipt.ProductionSourceHead != production.SourceHead ||
			!reflect.DeepEqual(receipt.AcceptedRunnerClassIDs, acceptedClasses) {
			return "", errors.New("resume receipt production binding mismatch")
		}
		receiptPath = resumePath
	} else {
		targets := make([]scaleSetSnapshot, 0, len(retirementTargets))
		for _, target := range retirementTargets {
			snap, err := snapshotTarget(ctx, token, sourceHead, target)
			if err != nil {
				return "", err
			}
			targets = append(targets, snap)
			fmt.Printf("LEGACY_SCALE_SET_DRAINED=%s available=0 acquired=0 assigned=0 running=0 registered=0 busy=0\n", target.LegacyName)
		}
		if err := ensureRootPrivateDir(receiptRoot); err != nil {
			return "", err
		}
		id := uuid.NewString()
		dir := filepath.Join(receiptRoot, id)
		if err := ensureRootPrivateDir(dir); err != nil {
			return "", err
		}
		receiptPath = filepath.Join(dir, "receipt.json")
		receipt = &retirementReceipt{
			SchemaVersion:                   1,
			Mode:                            mode,
			ReceiptID:                       id,
			SourceHead:                      sourceHead,
			ProductionTransaction:           productionTransaction,
			ProductionTransactionSHA256:     sha256Bytes(productionRaw),
			ProductionSourceHead:            production.SourceHead,
			ProductionGenerationSHA256:      production.ProductionGenerationSHA256,
			AcceptedRunnerClassIDs:          append([]string(nil), acceptedClasses...),
			PreservedLegacyBytesConfigState: true,
			PreservedUnacceptedScaleSets:    append([]string(nil), preservedUnacceptedLegacyScaleSets...),
			RollbackWindowRecordedAtUTC:     time.Now().UTC().Format(time.RFC3339Nano),
			Targets:                         targets,
			Phase:                           rollbackWindowPhase,
		}
		if err := atomicWriteReceipt(receiptPath, receipt); err != nil {
			return "", err
		}
		fmt.Printf("ROLLBACK_WINDOW_RECEIPT=%s\n", receiptPath)
		fmt.Println("LEGACY_BYTES_CONFIG_STATE_PRESERVED=PASS")
		fmt.Println("RESEARCH_LEGACY_SCALE_SETS_PRESERVED=PASS")
	}

	retiredCount := 0
	for i := range receipt.Targets {
		snap := &receipt.Targets[i]
		client, err := clientFor(snap.RepositoryURL, token, sourceHead)
		if err != nil {
			return receiptPath, err
		}
		if snap.Retired {
			current, err := client.GetRunnerScaleSet(ctx, runnerGroupID, snap.LegacyName)
			if err != nil {
				return receiptPath, err
			}
			if current != nil {
				return receiptPath, fmt.Errorf("retired scale set unexpectedly exists during resume: %s", snap.LegacyName)
			}
			retiredCount++
			continue
		}
		ss, err := verifySnapshotStillDrained(ctx, client, *snap)
		if err != nil {
			receipt.Phase = partialRetirementPhase
			receipt.LastError = err.Error()
			_ = atomicWriteReceipt(receiptPath, receipt)
			return receiptPath, err
		}
		if err := client.DeleteRunnerScaleSet(ctx, ss.ID); err != nil {
			receipt.Phase = partialRetirementPhase
			receipt.LastError = err.Error()
			_ = atomicWriteReceipt(receiptPath, receipt)
			return receiptPath, fmt.Errorf("delete legacy scale set %s: %w", snap.LegacyName, err)
		}
		current, err := client.GetRunnerScaleSet(ctx, runnerGroupID, snap.LegacyName)
		if err != nil {
			receipt.Phase = partialRetirementPhase
			receipt.LastError = err.Error()
			_ = atomicWriteReceipt(receiptPath, receipt)
			return receiptPath, err
		}
		if current != nil {
			receipt.Phase = partialRetirementPhase
			receipt.LastError = "deleted scale set still resolves by name"
			_ = atomicWriteReceipt(receiptPath, receipt)
			return receiptPath, fmt.Errorf("legacy scale set still exists after delete: %s", snap.LegacyName)
		}
		snap.Retired = true
		snap.RetiredAtUTC = time.Now().UTC().Format(time.RFC3339Nano)
		retiredCount++
		receipt.Phase = partialRetirementPhase
		receipt.LastError = ""
		if err := atomicWriteReceipt(receiptPath, receipt); err != nil {
			return receiptPath, err
		}
		fmt.Printf("LEGACY_SCALE_SET_RETIRED=%s id=%d\n", snap.LegacyName, snap.LegacyID)
	}

	if retiredCount != len(receipt.Targets) {
		return receiptPath, errors.New("not all accepted legacy scale sets retired")
	}
	if err := requireSystemdPostCommit(); err != nil {
		receipt.Phase = partialRetirementPhase
		receipt.LastError = err.Error()
		_ = atomicWriteReceipt(receiptPath, receipt)
		return receiptPath, err
	}
	receipt.Phase = completedPhase
	receipt.LastError = ""
	receipt.CompletedAtUTC = time.Now().UTC().Format(time.RFC3339Nano)
	if err := atomicWriteReceipt(receiptPath, receipt); err != nil {
		return receiptPath, err
	}
	return receiptPath, nil
}

func verifyCompletedRetirement(ctx context.Context, token, sourceHead, productionTransaction, receiptPath string) error {
	production, productionRaw, err := validateProductionReceipt(productionTransaction)
	if err != nil {
		return err
	}
	if err := requireSystemdPostCommit(); err != nil {
		return err
	}

	var receipt retirementReceipt
	raw, err := os.ReadFile(receiptPath)
	if err != nil {
		return err
	}
	info, err := os.Stat(receiptPath)
	if err != nil {
		return err
	}
	st, ok := info.Sys().(*syscall.Stat_t)
	if !ok || st.Uid != 0 || st.Gid != 0 || info.Mode().Perm() != 0o600 {
		return errors.New("verification receipt ownership/mode invalid")
	}
	if err := json.Unmarshal(raw, &receipt); err != nil {
		return err
	}
	if receipt.SchemaVersion != 1 || receipt.Mode != mode || receipt.Phase != completedPhase {
		return fmt.Errorf("retirement receipt is not completed: mode=%s phase=%s", receipt.Mode, receipt.Phase)
	}
	if receipt.SourceHead != sourceHead ||
		receipt.ProductionTransaction != productionTransaction ||
		receipt.ProductionTransactionSHA256 != sha256Bytes(productionRaw) ||
		receipt.ProductionGenerationSHA256 != production.ProductionGenerationSHA256 ||
		receipt.ProductionSourceHead != production.SourceHead ||
		!reflect.DeepEqual(receipt.AcceptedRunnerClassIDs, acceptedClasses) ||
		!receipt.PreservedLegacyBytesConfigState ||
		!reflect.DeepEqual(receipt.PreservedUnacceptedScaleSets, preservedUnacceptedLegacyScaleSets) {
		return errors.New("completed retirement receipt binding mismatch")
	}
	if len(receipt.Targets) != len(retirementTargets) {
		return errors.New("completed retirement target count mismatch")
	}

	for _, snap := range receipt.Targets {
		if !snap.Retired {
			return fmt.Errorf("retirement receipt contains non-retired target: %s", snap.LegacyName)
		}
		client, err := clientFor(snap.RepositoryURL, token, sourceHead)
		if err != nil {
			return err
		}
		legacy, err := client.GetRunnerScaleSet(ctx, runnerGroupID, snap.LegacyName)
		if err != nil {
			return err
		}
		if legacy != nil {
			return fmt.Errorf("retired legacy scale set still exists: %s", snap.LegacyName)
		}
		target, err := client.GetRunnerScaleSet(ctx, runnerGroupID, snap.TargetName)
		if err != nil {
			return err
		}
		if target == nil || target.ID != snap.TargetID || target.Name != snap.TargetName || target.RunnerGroupID != runnerGroupID {
			return fmt.Errorf("accepted v3 target changed after retirement: %s", snap.TargetName)
		}
		fmt.Printf("LEGACY_SCALE_SET_ABSENT=%s\n", snap.LegacyName)
		fmt.Printf("V3_TARGET_SCALE_SET_PRESENT=%s id=%d\n", snap.TargetName, snap.TargetID)
	}
	fmt.Println("RESEARCH_LEGACY_SCALE_SETS_PRESERVED=PASS")
	return nil
}

func main() {
	tokenFile := flag.String("token-file", "", "file containing a GitHub token with Actions scale-set administration access")
	sourceHead := flag.String("source-head", "", "exact reviewed workspace-control source head")
	productionTransaction := flag.String("production-transaction", "", "accepted production cutover transaction receipt")
	resumeReceipt := flag.String("resume-receipt", "", "existing partial retirement receipt to resume")
	verifyReceipt := flag.String("verify-receipt", "", "completed retirement receipt to verify in a fresh process")
	flag.Parse()

	if *tokenFile == "" || *sourceHead == "" || *productionTransaction == "" {
		fatalf("--token-file, --source-head, and --production-transaction are required")
	}
	if len(*sourceHead) != 40 || strings.Trim(*sourceHead, "0123456789abcdef") != "" {
		fatalf("source head must be a lowercase 40-hex SHA")
	}

	raw, err := os.ReadFile(*tokenFile)
	if err != nil {
		fatalf("read token file: %v", err)
	}
	token := strings.TrimSpace(string(raw))
	if token == "" {
		fatalf("token is empty")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
	defer cancel()
	if *verifyReceipt != "" {
		if *resumeReceipt != "" {
			fatalf("--verify-receipt and --resume-receipt are mutually exclusive")
		}
		if err := verifyCompletedRetirement(ctx, token, *sourceHead, *productionTransaction, *verifyReceipt); err != nil {
			fatalf("legacy retirement verification failed: %v", err)
		}
		fmt.Println("V3_LEGACY_SCALE_SET_RETIREMENT_VERIFY=PASS")
		return
	}
	receiptPath, err := applyRetirement(ctx, token, *sourceHead, *productionTransaction, *resumeReceipt)
	if err != nil {
		if receiptPath != "" {
			fmt.Fprintf(os.Stderr, "LEGACY_RETIREMENT_RECEIPT=%s\n", receiptPath)
		}
		fatalf("legacy retirement failed: %v", err)
	}
	fmt.Printf("LEGACY_RETIREMENT_RECEIPT=%s\n", receiptPath)
	fmt.Println("V3_LEGACY_SCALE_SET_RETIREMENT=PASS")
}
