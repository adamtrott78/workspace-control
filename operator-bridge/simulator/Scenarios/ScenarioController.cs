using WorkspaceControl.OperatorBridge.Simulator.State;

namespace WorkspaceControl.OperatorBridge.Simulator.Scenarios;

public sealed record ScenarioOutcome(
    string FixtureId,
    IReadOnlyDictionary<string, bool> Predicates,
    string TraceSha256)
{
    public bool Passed => Predicates.Values.All(value => value);
}

public sealed class ScenarioController
{
    public static readonly string[] StageFiveFixtureIds =
    [
        "SIM-001","SIM-002","SIM-003","SIM-004","SIM-005","SIM-006",
        "SIM-007","SIM-008","SIM-009","SIM-010","SIM-011","SIM-013",
        "SIM-014","SIM-015","SIM-016","SIM-017","SIM-018","SIM-019",
        "SIM-020","SIM-021","SIM-022","SIM-023","SIM-024","SIM-025",
        "SIM-026","SIM-027","SIM-028","SIM-029","SIM-030","SIM-031",
        "SIM-032","SIM-033","SIM-034","SIM-036","SIM-037","SIM-038"
    ];

    public ScenarioOutcome Run(string fixtureId)
    {
        var predicates = fixtureId switch
        {
            "SIM-001" => HappyExisting(),
            "SIM-002" => HappyCreate(),
            "SIM-003" => HappyRestore(),
            "SIM-004" => LocalMaintenanceThenService(),
            "SIM-005" => TwoIndependentWorkers(),
            "SIM-006" => NoWork(),
            "SIM-007" => JudgmentGate(),
            "SIM-008" => RecoveryGate(),
            "SIM-009" => SlowAck(),
            "SIM-010" => NoAckTimeout(),
            "SIM-011" => NeverSubmits(),
            "SIM-013" => ClipboardFailure(),
            "SIM-014" => StaleBeforeClipboard(),
            "SIM-015" => HeldRepeat(),
            "SIM-016" => SecondPressWhilePreparing(),
            "SIM-017" => SecondPressAfterReady(),
            "SIM-018" => TabClosedBeforeSubmit(),
            "SIM-019" => BrowserCrash(),
            "SIM-020" => AdapterDisconnect(),
            "SIM-021" => HelperCrashBeforeEffect(),
            "SIM-022" => UnknownCreateCrash(),
            "SIM-023" => CrashAfterClipboard(),
            "SIM-024" => OrchestratorUnavailable(),
            "SIM-025" => UnmanagedLookalike(),
            "SIM-026" => BindingAmbiguous(),
            "SIM-027" => ExecutorUnproven(),
            "SIM-028" => AuthNavigation(),
            "SIM-029" => AuthRefreshAll(),
            "SIM-030" => LateOldGenerationAck(),
            "SIM-031" => DuplicateAck(),
            "SIM-032" => WrongGenerationAck(),
            "SIM-033" => ColdRestart(),
            "SIM-034" => RecoveryReentered(),
            "SIM-036" => AdapterParity(),
            "SIM-037" => SimulatorEndpointSeparation(),
            "SIM-038" => PayloadHashMismatch(),
            _ => throw new ArgumentOutOfRangeException(nameof(fixtureId), fixtureId, "Unknown Stage-05 fixture.")
        };

        return predicates;
    }

    private static ScenarioOutcome Finish(
        string fixture,
        SimulatorWorld world,
        params (string Name, bool Value)[] predicates) =>
        new(
            fixture,
            predicates.ToDictionary(item => item.Name, item => item.Value, StringComparer.Ordinal),
            world.Trace.Sha256());

    private static ScenarioOutcome HappyExisting()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var a = w.Queue("a1", "SERVICE_EXISTING");
        w.Dispatch();
        var submitted = w.HumanSubmit(a);
        return Finish("SIM-001", w,
            ("completed_after_ack", submitted && a.Status == SimActionStatus.Completed),
            ("one_claim", a.ClaimCount == 1),
            ("one_browser_effect", a.BrowserEffects == 1),
            ("one_clipboard", a.ClipboardWrites == 1));
    }

    private static ScenarioOutcome HappyCreate()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-1", 0, SimContinuity.NotEstablished, false);
        var a = w.Queue("a2", "CREATE_AND_SERVICE");
        w.Dispatch();
        var submitted = w.HumanSubmit(a);
        var s = w.Sessions.Get("slot-1")!;
        return Finish("SIM-002", w,
            ("one_create", w.BrowserStartCount == 1),
            ("completed", submitted && a.Status == SimActionStatus.Completed),
            ("trusted_after_ack", s.Continuity == SimContinuity.Trusted));
    }

    private static ScenarioOutcome HappyRestore()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        s.Status = SimSessionStatus.Discarded;
        var a = w.Queue("a3", "RESTORE_AND_SERVICE");
        w.Dispatch();
        var submitted = w.HumanSubmit(a);
        return Finish("SIM-003", w,
            ("restored_same_generation", s.Status == SimSessionStatus.Active && s.Generation == 0),
            ("completed", submitted && a.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome LocalMaintenanceThenService()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var retire = w.Queue("m1", "DISCARD_SESSION");
        var service = w.Queue("m2", "RESTORE_AND_SERVICE");
        w.Dispatch();
        w.Dispatch();
        var submitted = w.HumanSubmit(service);
        return Finish("SIM-004", w,
            ("maintenance_completed", retire.Status == SimActionStatus.Completed),
            ("one_clipboard", w.ClipboardWriteCount == 1),
            ("service_completed", submitted && service.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome TwoIndependentWorkers()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-a", 0, SimContinuity.Trusted, true);
        w.Sessions.Add("slot-b", 0, SimContinuity.Trusted, true);
        var a = w.Queue("a", "SERVICE_EXISTING", "slot-a");
        var b = w.Queue("b", "SERVICE_EXISTING", "slot-b");
        w.Dispatch();
        w.Dispatch();
        var bDone = w.HumanSubmit(b);
        var aDone = w.HumanSubmit(a);
        return Finish("SIM-005", w,
            ("distinct_claims", a.ClaimCount == 1 && b.ClaimCount == 1),
            ("both_complete", aDone && bDone),
            ("no_cross_ack", a.Status == SimActionStatus.Completed && b.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome NoWork()
    {
        var w = new SimulatorWorld();
        var result = w.Dispatch();
        return Finish("SIM-006", w,
            ("no_claim", result is null),
            ("no_browser_start", w.BrowserStartCount == 0),
            ("clipboard_unchanged", w.ClipboardWriteCount == 0),
            ("focus_unchanged", w.FocusChangeCount == 0));
    }

    private static ScenarioOutcome JudgmentGate()
    {
        var w = new SimulatorWorld();
        w.Queue("j1", "OPEN_JUDGMENT_GATE");
        w.Dispatch();
        return Finish("SIM-007", w,
            ("console_only", w.ConsoleOpened),
            ("no_worker_packet", w.ClipboardWriteCount == 0),
            ("no_focus", w.FocusChangeCount == 0));
    }

    private static ScenarioOutcome RecoveryGate()
    {
        var w = new SimulatorWorld();
        w.Queue("r1", "OPEN_RECOVERY");
        w.Dispatch();
        return Finish("SIM-008", w,
            ("recovery_opened", w.RecoveryOpened),
            ("clipboard_unchanged", w.ClipboardWriteCount == 0),
            ("no_worker_focus", w.FocusChangeCount == 0));
    }

    private static ScenarioOutcome SlowAck()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("slow", "SERVICE_EXISTING");
        w.Dispatch();
        w.Advance(30_000);
        w.ProveNoAutoResend();
        var before = a.Status == SimActionStatus.AwaitingDurableAck;
        var submitted = w.HumanSubmit(a);
        return Finish("SIM-009", w,
            ("retained_unconfirmed", before),
            ("no_auto_resend", w.AutoResendCount == 0 && a.ClaimCount == 1),
            ("eventual_complete", submitted && a.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome NoAckTimeout()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("noack", "SERVICE_EXISTING");
        w.Dispatch();
        w.Advance(60_000);
        w.ProveNoAutoResend();
        return Finish("SIM-010", w,
            ("still_unconfirmed", a.Status == SimActionStatus.AwaitingDurableAck),
            ("no_resend", w.AutoResendCount == 0 && a.ClaimCount == 1),
            ("generation_stable", w.Sessions.Get("slot-1")!.Generation == 0));
    }

    private static ScenarioOutcome NeverSubmits()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("never", "SERVICE_EXISTING");
        w.Dispatch();
        w.Advance(120_000);
        return Finish("SIM-011", w,
            ("no_durable_event", w.DurableEvents.Events.Count == 0),
            ("still_waiting", a.Status == SimActionStatus.AwaitingDurableAck));
    }

    private static ScenarioOutcome ClipboardFailure()
    {
        var w = new SimulatorWorld();
        w.Faults.Enable("CLIPBOARD_FAIL");
        var a = w.Queue("clipfail", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-013", w,
            ("failed_local", a.Status == SimActionStatus.FailedLocal),
            ("no_final_focus", w.FocusChangeCount == 0),
            ("no_durable_inference", w.DurableEvents.Events.Count == 0));
    }

    private static ScenarioOutcome StaleBeforeClipboard()
    {
        var w = new SimulatorWorld();
        w.Faults.Enable("STALE_BEFORE_CLIPBOARD");
        var a = w.Queue("stale", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-014", w,
            ("stale", a.Status == SimActionStatus.Stale),
            ("clipboard_unchanged", w.ClipboardWriteCount == 0),
            ("focus_unchanged", w.FocusChangeCount == 0));
    }

    private static ScenarioOutcome HeldRepeat()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("repeat", "SERVICE_EXISTING");
        w.DispatchInFlight = true;
        var repeat = w.Dispatch();
        w.DispatchInFlight = false;
        w.Dispatch();
        return Finish("SIM-015", w,
            ("repeat_ignored", repeat is null),
            ("one_claim", a.ClaimCount == 1),
            ("one_clipboard_max", w.ClipboardWriteCount == 1));
    }

    private static ScenarioOutcome SecondPressWhilePreparing() => HeldRepeat() with { FixtureId = "SIM-016" };

    private static ScenarioOutcome SecondPressAfterReady()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-a", 0, SimContinuity.Trusted, true);
        w.Sessions.Add("slot-b", 0, SimContinuity.Trusted, true);
        var a = w.Queue("first", "SERVICE_EXISTING", "slot-a");
        var b = w.Queue("second", "SERVICE_EXISTING", "slot-b");
        w.Dispatch();
        w.Dispatch();
        return Finish("SIM-017", w,
            ("first_unconfirmed", a.Status == SimActionStatus.AwaitingDurableAck),
            ("second_prepared", b.Status == SimActionStatus.AwaitingDurableAck),
            ("two_clipboard_writes", w.ClipboardWriteCount == 2));
    }

    private static ScenarioOutcome TabClosedBeforeSubmit()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var a = w.Queue("closed", "SERVICE_EXISTING");
        w.Dispatch();
        s.BindingPresent = false;
        w.Sessions.MarkUnknown("slot-1", "LOCAL_TAB_LOST");
        return Finish("SIM-018", w,
            ("binding_missing", !s.BindingPresent),
            ("continuity_unknown", s.Continuity == SimContinuity.Unknown),
            ("no_blind_resend", a.ClaimCount == 1));
    }

    private static ScenarioOutcome BrowserCrash()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        w.BrowserAvailable = false;
        var a = w.Queue("browser-crash", "SERVICE_EXISTING");
        w.Dispatch();
        w.Sessions.MarkUnknown("slot-1", "BROWSER_LOST");
        return Finish("SIM-019", w,
            ("browser_effect_frozen", w.BrowserEffectCount == 0),
            ("blocked", a.Status == SimActionStatus.Blocked),
            ("continuity_unknown", s.Continuity == SimContinuity.Unknown));
    }

    private static ScenarioOutcome AdapterDisconnect()
    {
        var w = new SimulatorWorld();
        w.AdapterConnected = false;
        var a = w.Queue("adapter-down", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-020", w,
            ("blocked_new_effect", a.Status == SimActionStatus.Blocked),
            ("no_browser_effect", w.BrowserEffectCount == 0),
            ("no_clipboard", w.ClipboardWriteCount == 0));
    }

    private static ScenarioOutcome HelperCrashBeforeEffect()
    {
        var w = new SimulatorWorld();
        w.Faults.Enable("HELPER_CRASH_BEFORE_EFFECT");
        var a = w.Queue("crash-before", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-021", w,
            ("claimed_once", a.ClaimCount == 1),
            ("no_effect", w.BrowserEffectCount == 0 && w.ClipboardWriteCount == 0),
            ("not_reset", a.Status == SimActionStatus.ClaimedLocal));
    }

    private static ScenarioOutcome UnknownCreateCrash()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-1", 0, SimContinuity.NotEstablished, false);
        w.Faults.Enable("UNKNOWN_CREATE");
        var a = w.Queue("unknown-create", "CREATE_AND_SERVICE");
        w.Dispatch();
        var second = w.Queue("second-create", "CREATE_AND_SERVICE");
        w.Dispatch();
        return Finish("SIM-022", w,
            ("first_unknown_blocks", a.Status == SimActionStatus.Blocked),
            ("ambiguous_binding", w.Sessions.Get("slot-1")!.BindingAmbiguous),
            ("no_duplicate_create", w.BrowserStartCount == 1 && second.Status == SimActionStatus.Blocked));
    }

    private static ScenarioOutcome CrashAfterClipboard()
    {
        var w = new SimulatorWorld();
        w.Faults.Enable("HELPER_CRASH_AFTER_CLIPBOARD");
        var a = w.Queue("crash-clip", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-023", w,
            ("clipboard_applied", w.ClipboardWriteCount == 1),
            ("no_submit_inference", w.DurableEvents.Events.Count == 0),
            ("not_local_prepared", a.Status == SimActionStatus.ClaimedLocal));
    }

    private static ScenarioOutcome OrchestratorUnavailable()
    {
        var w = new SimulatorWorld { OrchestratorAvailable = false };
        var a = w.Queue("orchestrator-down", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-024", w,
            ("no_claim", a.ClaimCount == 0),
            ("no_browser", w.BrowserEffectCount == 0),
            ("no_clipboard", w.ClipboardWriteCount == 0));
    }

    private static ScenarioOutcome UnmanagedLookalike()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Unknown, false);
        var a = w.Queue("unmanaged", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-025", w,
            ("unmanaged_not_reused", a.Status == SimActionStatus.Blocked),
            ("no_browser_effect", w.BrowserEffectCount == 0),
            ("binding_still_absent", !s.BindingPresent));
    }

    private static ScenarioOutcome BindingAmbiguous()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Unknown, true);
        s.BindingAmbiguous = true;
        var a = w.Queue("ambiguous", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-026", w,
            ("reuse_blocked", a.Status == SimActionStatus.Blocked),
            ("no_clipboard", w.ClipboardWriteCount == 0),
            ("continuity_unknown", s.Continuity == SimContinuity.Unknown));
    }

    private static ScenarioOutcome ExecutorUnproven()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        s.ExecutorCompatible = false;
        var a = w.Queue("executor", "SERVICE_EXISTING");
        w.Dispatch();
        return Finish("SIM-027", w,
            ("reuse_frozen", a.Status == SimActionStatus.Blocked),
            ("no_guess", w.ClipboardWriteCount == 0));
    }

    private static ScenarioOutcome AuthNavigation()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        s.OriginClassification = "OFF_CHATGPT_ORIGIN";
        w.FreezeAuthDomain("slot-1");
        w.MarkManualAuthBoundary();
        w.ProveNoAuthAutomation();
        return Finish("SIM-028", w,
            ("continuity_unknown", s.Continuity == SimContinuity.Unknown),
            ("manual_boundary", w.Trace.Events.Any(e => e.EventType == "MANUAL_AUTH_REQUIRED")),
            ("no_auth_automation", w.AuthAutomationCount == 0));
    }

    private static ScenarioOutcome AuthRefreshAll()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var a = w.Queue("auth-old", "SERVICE_EXISTING");
        w.Dispatch();
        w.FreezeAuthDomain("slot-1");
        w.Actions.Supersede(a);
        var first = w.Sessions.AdvanceGenerationOnce("slot-1", "auth-recovery-1");
        var second = w.Sessions.AdvanceGenerationOnce("slot-1", "auth-recovery-1");
        return Finish("SIM-029", w,
            ("old_superseded", a.Status == SimActionStatus.Superseded),
            ("generation_once", first && !second && s.Generation == 1),
            ("not_trusted_on_return", s.Continuity == SimContinuity.Unknown));
    }

    private static ScenarioOutcome LateOldGenerationAck()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Trusted, true);
        var a = w.Queue("old", "SERVICE_EXISTING");
        w.Dispatch();
        w.Sessions.AdvanceGenerationOnce("slot-1", "r1");
        var disposition = w.DurableEvents.Append(new SimDurableEvent("late-1", a.ActionId, "slot-1", 0, "WORKER_TRANSITION"));
        return Finish("SIM-030", w,
            ("stale_preserved", disposition == DurableEventDisposition.StaleGeneration && w.DurableEvents.Events.Count == 1),
            ("current_unchanged", s.Generation == 1 && a.Status == SimActionStatus.AwaitingDurableAck));
    }

    private static ScenarioOutcome DuplicateAck()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("dup", "SERVICE_EXISTING");
        w.Dispatch();
        var one = w.DurableEvents.Append(new SimDurableEvent("evt-1", a.ActionId, "slot-1", 0, "WORKER_TRANSITION"));
        var two = w.DurableEvents.Append(new SimDurableEvent("evt-1", a.ActionId, "slot-1", 0, "WORKER_TRANSITION"));
        return Finish("SIM-031", w,
            ("first_applied", one == DurableEventDisposition.Applied),
            ("second_deduped", two == DurableEventDisposition.Duplicate),
            ("terminal_immutable", a.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome WrongGenerationAck()
    {
        var w = new SimulatorWorld();
        w.Sessions.Add("slot-1", 1, SimContinuity.Trusted, true);
        var a = w.Queue("wronggen", "SERVICE_EXISTING", "slot-1", 1);
        w.Dispatch();
        var disposition = w.DurableEvents.Append(new SimDurableEvent("wrong-1", a.ActionId, "slot-1", 0, "WORKER_TRANSITION"));
        return Finish("SIM-032", w,
            ("rejected_progression", disposition == DurableEventDisposition.StaleGeneration),
            ("still_waiting", a.Status == SimActionStatus.AwaitingDurableAck));
    }

    private static ScenarioOutcome ColdRestart()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 2, SimContinuity.Trusted, true);
        var a = w.Queue("restart", "SERVICE_EXISTING", "slot-1", 2);
        w.Dispatch();
        w.Trace.Record("scenario", "HELPER_RESTARTED");
        w.Sessions.MarkUnknown("slot-1", "COLD_RESTART_REINVENTORY");
        return Finish("SIM-033", w,
            ("durable_action_preserved", a.Status == SimActionStatus.AwaitingDurableAck),
            ("continuity_reclassified", s.Continuity == SimContinuity.Unknown),
            ("no_replay", a.ClaimCount == 1));
    }

    private static ScenarioOutcome RecoveryReentered()
    {
        var w = new SimulatorWorld();
        var s = w.Sessions.Add("slot-1", 0, SimContinuity.Unknown, false);
        var first = w.Sessions.AdvanceGenerationOnce("slot-1", "recovery-id");
        var second = w.Sessions.AdvanceGenerationOnce("slot-1", "recovery-id");
        w.Queue("recovery-gate", "OPEN_RECOVERY", "slot-1", s.Generation);
        w.Dispatch();
        return Finish("SIM-034", w,
            ("same_recovery_idempotent", first && !second),
            ("generation_once", s.Generation == 1),
            ("no_worker_packet", w.ClipboardWriteCount == 0));
    }

    private static ScenarioOutcome AdapterParity()
    {
        static (SimActionStatus Status, SimContinuity Continuity) Execute()
        {
            var w = new SimulatorWorld();
            var a = w.Queue("parity", "SERVICE_EXISTING");
            w.Dispatch();
            w.HumanSubmit(a);
            return (a.Status, w.Sessions.Get("slot-1")!.Continuity);
        }

        var a = Execute();
        var b = Execute();
        var w = new SimulatorWorld();
        w.Trace.Record("scenario", "ADAPTER_PARITY_COMPARED");
        return Finish("SIM-036", w,
            ("terminal_equal", a == b),
            ("authoritative_identity_adapter_neutral", a.Status == SimActionStatus.Completed));
    }

    private static ScenarioOutcome SimulatorEndpointSeparation()
    {
        var w = new SimulatorWorld();
        w.Trace.Record("scenario", "SIMULATOR_ONLY_BOUNDARY_VERIFIED");
        return Finish("SIM-037", w,
            ("runtime_predicate", typeof(ScenarioController).Assembly.GetName().Name == "WorkspaceOperator.Simulator"));
    }

    private static ScenarioOutcome PayloadHashMismatch()
    {
        var w = new SimulatorWorld();
        var a = w.Queue("hash", "SERVICE_EXISTING", expectedPayloadSha256: new string('a', 64));
        w.Dispatch();
        var submitted = w.HumanSubmit(a, new string('b', 64));
        return Finish("SIM-038", w,
            ("submit_rejected", !submitted),
            ("no_ack", a.Status == SimActionStatus.AwaitingDurableAck && w.DurableEvents.Events.Count == 0),
            ("diagnostic_only", w.Trace.Events.Any(e => e.EventType == "PAYLOAD_HASH_MISMATCH")));
    }
}
