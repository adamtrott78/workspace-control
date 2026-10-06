package main

import (
	"bufio"
	"context"
	"encoding/json"
	"net"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestProvisionRequestSchemaIsExact(t *testing.T) {
	req := provisionRequest{
		SchemaVersion: 1,
		RequestID:     "01234567-89ab-4cde-8fab-0123456789ab",
		ProjectID:     "research-engine",
		Profile:       "cpu-test",
		RunnerName:    "lambda-research-engine-test",
		JITConfig:     "opaque-secret",
	}
	raw, err := json.Marshal(req)
	if err != nil {
		t.Fatal(err)
	}
	var got map[string]any
	if err := json.Unmarshal(raw, &got); err != nil {
		t.Fatal(err)
	}
	want := []string{"jit_config", "profile", "project_id", "request_id", "runner_name", "schema_version"}
	gotKeys := make([]string, 0, len(got))
	for _, key := range want {
		if _, ok := got[key]; ok {
			gotKeys = append(gotKeys, key)
		}
	}
	if !reflect.DeepEqual(gotKeys, want) || len(got) != len(want) {
		t.Fatalf("unexpected request schema: %#v", got)
	}
}

func TestReadSecretFileRejectsBroadPermissions(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "token")
	if err := os.WriteFile(path, []byte("secret\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := readSecretFile(path); err == nil {
		t.Fatal("broad credential permissions accepted")
	}
	if err := os.Chmod(path, 0o600); err != nil {
		t.Fatal(err)
	}
	value, err := readSecretFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if value != "secret" {
		t.Fatalf("unexpected secret value %q", value)
	}
}

func TestProvisionerSocketReceivesJITButResponseDoesNotEchoIt(t *testing.T) {
	dir := t.TempDir()
	socketPath := filepath.Join(dir, "provisioner.sock")
	ln, err := net.Listen("unix", socketPath)
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()

	secret := "encoded-jit-secret"
	received := make(chan provisionRequest, 1)
	go func() {
		conn, err := ln.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		var req provisionRequest
		if err := json.NewDecoder(bufio.NewReader(conn)).Decode(&req); err != nil {
			return
		}
		received <- req
		_ = json.NewEncoder(conn).Encode(provisionResponse{
			SchemaVersion: 1,
			Status:        "ACCEPTED",
			RequestID:     req.RequestID,
		})
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	response, err := sendProvisionRequest(ctx, socketPath, provisionRequest{
		SchemaVersion: 1,
		RequestID:     "01234567-89ab-4cde-8fab-0123456789ab",
		ProjectID:     "research-engine",
		Profile:       "cpu-test",
		RunnerName:    "lambda-research-engine-test",
		JITConfig:     secret,
	})
	if err != nil {
		t.Fatal(err)
	}
	if response.Status != "ACCEPTED" {
		t.Fatalf("unexpected status %s", response.Status)
	}
	req := <-received
	if req.JITConfig != secret {
		t.Fatal("JIT config was not delivered to provisioner")
	}
	encoded, _ := json.Marshal(response)
	if string(encoded) == secret || contains(string(encoded), secret) {
		t.Fatal("provisioner response echoed JIT secret")
	}
}

func TestPilotConstantsAreFixed(t *testing.T) {
	if defaultProjectID != "research-engine" || defaultProfile != "cpu-test" || gpuProfile != "gpu-small" {
		t.Fatal("pilot authority changed")
	}
	if defaultScaleSetName != "lambda-research-engine" || gpuScaleSetName != "lambda-research-engine-gpu" || maxRunners != 1 {
		t.Fatal("pilot scale-set capacity changed")
	}
	if !controllerMappingAllowed(defaultScaleSetName, defaultProfile) {
		t.Fatal("CPU controller mapping rejected")
	}
	if !controllerMappingAllowed(gpuScaleSetName, gpuProfile) {
		t.Fatal("GPU controller mapping rejected")
	}
	if controllerMappingAllowed(defaultScaleSetName, gpuProfile) ||
		controllerMappingAllowed(gpuScaleSetName, defaultProfile) ||
		controllerMappingAllowed("lambda-research-engine-heavy", "gpu-heavy") {
		t.Fatal("unexpected controller mapping accepted")
	}
}

func TestRunnerNamesAreProfileScoped(t *testing.T) {
	cpu, err := runnerName(defaultProfile)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(cpu, "lambda-research-engine-") || strings.HasPrefix(cpu, "lambda-research-engine-gpu-") {
		t.Fatalf("unexpected CPU runner name %q", cpu)
	}

	gpu, err := runnerName(gpuProfile)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(gpu, "lambda-research-engine-gpu-") {
		t.Fatalf("unexpected GPU runner name %q", gpu)
	}
	if _, err := runnerName("gpu-heavy"); err == nil {
		t.Fatal("gpu-heavy runner name accepted")
	}
}

func contains(haystack, needle string) bool {
	if len(needle) == 0 {
		return true
	}
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}
