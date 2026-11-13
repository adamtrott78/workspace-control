import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

compiler = load_module('lambda_ci_policy_compiler_dual_test', 'scripts/lambda_ci_policy_compiler.py')

# The activation helper imports sibling modules by normal name.
sys.modules['lambda_ci_policy_compiler'] = compiler
reconciler = load_module('lambda_ci_v3_reconciler', 'scripts/lambda_ci_v3_reconciler.py')
sys.modules['lambda_ci_v3_reconciler'] = reconciler
base = load_module(
    'lambda_ci_v3_padataset_scientific_activation_v1',
    'scripts/lambda_ci_v3_padataset_scientific_activation_v1.py',
)
sys.modules['lambda_ci_v3_padataset_scientific_activation_v1'] = base
dual = load_module(
    'lambda_ci_v3_padataset_scientific_dual_lane_v1',
    'scripts/lambda_ci_v3_padataset_scientific_dual_lane_v1.py',
)


class PadatasetScientificDualLaneActivationTests(unittest.TestCase):
    def candidate(self):
        return compiler.compile_policy(ROOT)['root_projection']

    def predecessor(self):
        candidate = self.candidate()
        current = copy.deepcopy(candidate)
        current['runner_classes'].pop(dual.TARGET_CLASS)
        current['host_resource_policy']['migration_mode']['host_max_active_runners'] = 1
        current['host_resource_policy']['project_limits']['padataset']['max_active_runners'] = 1
        for policy in current['runner_classes'].values():
            if policy['project_id'] == 'padataset':
                policy['project_max_active_runners'] = 1
                semantic = {
                    k: v for k, v in policy.items()
                    if k not in {'control_plane_generation_sha256', 'root_envelope_sha256'}
                }
                policy['root_envelope_sha256'] = compiler.sha256_object(semantic)
        return current

    def test_generation_accepts_only_bounded_padataset_concurrency_delta(self):
        previous, current = dual._validate_generation(
            self.predecessor(), self.candidate()
        )
        self.assertNotIn(dual.TARGET_CLASS, previous)
        self.assertIn(dual.TARGET_CLASS, current)
        self.assertEqual(len(current), len(previous) + 1)

    def test_generation_rejects_unrelated_project_limit_widening(self):
        candidate = self.candidate()
        candidate['host_resource_policy']['project_limits']['research-engine']['max_active_runners'] = 2
        with self.assertRaisesRegex(dual.DualLaneActivationError, 'unrelated project limit'):
            dual._validate_generation(self.predecessor(), candidate)

    def test_generation_rejects_lane_b_gpu_overlap(self):
        candidate = self.candidate()
        lane = candidate['runner_classes'][dual.TARGET_CLASS]
        lane['exclusive_resource_claims'] = [f'gpu:{dual.GPU0}']
        with self.assertRaisesRegex(dual.DualLaneActivationError, 'GPU1 claim mismatch'):
            dual._validate_generation(self.predecessor(), candidate)

    def test_static_transaction_orders_quiescence_before_mutation(self):
        source = (ROOT / 'scripts/lambda_ci_v3_padataset_scientific_dual_lane_v1.py').read_text()
        expand = source[source.index('def expand_inactive('):source.index('def activate(')]
        first_quiescent = expand.index('base._require_quiescent(systemd)')
        consume = expand.index('_consume_authority(authority, authority_raw)')
        stop = expand.index('systemd.stop(PROVISIONER_UNIT)')
        second_quiescent = expand.index('base._require_quiescent(systemd)', stop)
        first_write = expand.index('base._atomic_file(path, raw, mode)')
        self.assertLess(first_quiescent, consume)
        self.assertLess(consume, stop)
        self.assertLess(stop, second_quiescent)
        self.assertLess(second_quiescent, first_write)

    def test_activation_requires_fresh_zero_work_preflight(self):
        source = (ROOT / 'scripts/lambda_ci_v3_padataset_scientific_dual_lane_v1.py').read_text()
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_scientific_workflow_runs": 0',
            'PREFLIGHT_MAX_SECONDS = 15 * 60',
            'base._require_quiescent(systemd)',
            'ACTIVATE_PADATASET_SCIENTIFIC_DUAL_LANE_V1',
        ):
            self.assertIn(marker, source)

    def test_authority_consumption_is_dual_lane_namespaced_and_single_use(self):
        source = (ROOT / 'scripts/lambda_ci_v3_padataset_scientific_dual_lane_v1.py').read_text()
        self.assertIn("AUTHORITY_ROOT = STATE_ROOT / \"authority-consumption\"", source)
        self.assertIn('os.O_EXCL', source)
        self.assertIn('dual-lane authorization already consumed', source)
        self.assertNotIn('return base._consume_authority(value, raw)', source)

    def test_lane_b_only_activation_and_rollback_markers_exist(self):
        source = (ROOT / 'scripts/lambda_ci_v3_padataset_scientific_dual_lane_v1.py').read_text()
        activate = source[source.index('def activate('):source.index('def main()')]
        self.assertIn('systemd.start(TARGET_UNIT)', activate)
        self.assertIn('systemd.enable(TARGET_UNIT)', activate)
        self.assertIn('systemd.disable(TARGET_UNIT)', activate)
        self.assertIn('systemd.stop(TARGET_UNIT)', activate)
        self.assertIn('ROLLED_BACK_TO_INSTALLED_INACTIVE', activate)


if __name__ == '__main__':
    unittest.main()
