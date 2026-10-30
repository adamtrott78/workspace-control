package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/actions/scaleset"
)

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(1)
}

func clientFor(url, token, sourceHead string) *scaleset.Client {
	client, err := scaleset.NewClientWithPersonalAccessToken(
		scaleset.NewClientWithPersonalAccessTokenConfig{
			GitHubConfigURL:     url,
			PersonalAccessToken: token,
			SystemInfo: scaleset.SystemInfo{
				System:    "workspace-control",
				Version:   "v3",
				CommitSHA: sourceHead,
				Subsystem: "lambda-ci-v3-canary-preflight",
			},
		},
	)
	if err != nil {
		fatalf("create scale-set client for %s: %v", url, err)
	}
	return client
}

func requireDrained(ctx context.Context, client *scaleset.Client, name string) {
	ss, err := client.GetRunnerScaleSet(ctx, 1, name)
	if err != nil {
		fatalf("get legacy scale set %s: %v", name, err)
	}
	if ss == nil {
		fatalf("active legacy scale set %s is missing", name)
	}
	if ss.Statistics == nil {
		fatalf("legacy scale set %s lacks statistics", name)
	}
	if ss.Statistics.TotalAssignedJobs != 0 || ss.Statistics.TotalRunningJobs != 0 {
		fatalf(
			"legacy scale set %s is not drained: assigned=%d running=%d",
			name,
			ss.Statistics.TotalAssignedJobs,
			ss.Statistics.TotalRunningJobs,
		)
	}
	fmt.Printf(
		"LEGACY_SCALE_SET_DRAINED=%s assigned=0 running=0\n",
		name,
	)
}

func main() {
	tokenFile := flag.String("token-file", "", "controller token file")
	legacySets := flag.String("legacy-scalesets", "", "tab-separated URL/name file")
	sourceHead := flag.String("source-head", "", "exact reviewed source head")
	targetName := flag.String("target-name", "", "target v3 runner scale-set name")
	flag.Parse()

	if *tokenFile == "" || *legacySets == "" || *sourceHead == "" || *targetName == "" {
		fatalf("all flags are required")
	}

	tokenRaw, err := os.ReadFile(*tokenFile)
	if err != nil {
		fatalf("read token: %v", err)
	}
	token := strings.TrimSpace(string(tokenRaw))
	if token == "" {
		fatalf("token is empty")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	file, err := os.Open(*legacySets)
	if err != nil {
		fatalf("open legacy scale-set list: %v", err)
	}
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		fields := strings.Split(scanner.Text(), "\t")
		if len(fields) != 2 {
			fatalf("invalid legacy scale-set record")
		}
		requireDrained(
			ctx,
			clientFor(fields[0], token, *sourceHead),
			fields[1],
		)
	}
	if err := scanner.Err(); err != nil {
		fatalf("read legacy scale-set list: %v", err)
	}
	if err := file.Close(); err != nil {
		fatalf("close legacy scale-set list: %v", err)
	}

	targetClient := clientFor(
		"https://github.com/adamtrott78/workspace-control",
		token,
		*sourceHead,
	)
	target, err := targetClient.GetRunnerScaleSet(ctx, 1, *targetName)
	if err != nil {
		fatalf("get target scale set: %v", err)
	}
	if target == nil {
		target, err = targetClient.CreateRunnerScaleSet(
			ctx,
			&scaleset.RunnerScaleSet{
				Name:          *targetName,
				RunnerGroupID: 1,
				RunnerSetting: scaleset.RunnerSetting{
					DisableUpdate: true,
				},
			},
		)
		if err != nil {
			fatalf("create target scale set: %v", err)
		}
		fmt.Printf("V3_SCALE_SET_CREATED=%s id=%d\n", target.Name, target.ID)
	}

	target, err = targetClient.GetRunnerScaleSet(ctx, 1, *targetName)
	if err != nil {
		fatalf("re-read target scale set: %v", err)
	}
	if target == nil || target.ID <= 0 || target.Name != *targetName || target.RunnerGroupID != 1 {
		fatalf("target scale-set identity mismatch")
	}
	if target.Statistics == nil {
		fatalf("target scale set lacks statistics")
	}
	if target.Statistics.TotalAssignedJobs != 0 || target.Statistics.TotalRunningJobs != 0 {
		fatalf(
			"target v3 scale set already has work: assigned=%d running=%d",
			target.Statistics.TotalAssignedJobs,
			target.Statistics.TotalRunningJobs,
		)
	}

	fmt.Printf("V3_SCALE_SET_READY=%s\n", target.Name)
	fmt.Printf("V3_SCALE_SET_ID=%d\n", target.ID)
	fmt.Println("V3_SCALE_SET_ASSIGNED=0")
	fmt.Println("V3_SCALE_SET_RUNNING=0")
}
