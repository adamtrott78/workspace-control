import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text())

GPU0 = 'GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea'
GPU1 = 'GPU-cfed3394-a935-63aa-9325-c4cae7b568b6'

class PadatasetScientificDualLaneTests(unittest.TestCase):
    def test_resource_allocator_and_project_caps_are_bounded_at_two(self):
        host = load('architecture/lambda-ci-host-resource-policy.v1.json')
        self.assertEqual(host['migration_mode']['host_max_active_runners'], 2)
        self.assertEqual(host['project_limits']['padataset']['max_active_runners'], 2)
        self.assertEqual(host['project_limits']['workspace-control']['max_active_runners'], 1)
        self.assertEqual(host['project_limits']['research-engine']['max_active_runners'], 1)

    def test_scientific_lanes_have_disjoint_exact_gpu_claims(self):
        workload = load('architecture/lambda-ci-workload-policy.v1.json')
        a = workload['resource_classes']['scientific_gpu_single_v1']
        b = workload['resource_classes']['scientific_gpu_single_2_v1']
        self.assertEqual(a['gpu_uuids'], [GPU0])
        self.assertEqual(b['gpu_uuids'], [GPU1])
        self.assertTrue(set(a['gpu_uuids']).isdisjoint(b['gpu_uuids']))
        self.assertEqual(a['gpu_count'], 1)
        self.assertEqual(b['gpu_count'], 1)

    def test_systemd_profiles_expose_only_the_bound_gpu(self):
        profiles = load('architecture/lambda-ci-systemd-profiles.v1.json')['profiles']
        a = profiles['gpu-scientific-single']
        b = profiles['gpu-scientific-single-2']
        self.assertEqual(a['CUDA_VISIBLE_DEVICES'], GPU0)
        self.assertEqual(b['CUDA_VISIBLE_DEVICES'], GPU1)
        self.assertTrue(any(GPU0 in row for row in a['DeviceAllow_candidate']))
        self.assertFalse(any(GPU1 in row for row in a['DeviceAllow_candidate']))
        self.assertTrue(any(GPU1 in row for row in b['DeviceAllow_candidate']))
        self.assertFalse(any(GPU0 in row for row in b['DeviceAllow_candidate']))

    def test_lane_b_is_independent_and_fail_closed_in_overlay(self):
        catalog = load('architecture/lambda-ci-runner-class-catalog.v1.json')
        p = catalog['projects']['padataset']
        a = p['runner_classes']['padataset-scientific-single-gpu-v1']
        b = p['runner_classes']['padataset-scientific-single-gpu-2-v1']
        self.assertNotEqual(a['scale_set_name'], b['scale_set_name'])
        self.assertNotEqual(a['controller_peer']['unix_user'], b['controller_peer']['unix_user'])
        self.assertEqual(p['routes']['scientific-single-gpu-2']['ingress']['command'], '/lambda-scientific-2')
        overlay = load('architecture/lambda-ci-deployment-overlay.v1.json')
        self.assertEqual(overlay['classes']['padataset-scientific-single-gpu-2-v1']['install_state'], 'NOT_INSTALLED')
        self.assertEqual(overlay['classes']['padataset-scientific-single-gpu-2-v1']['controller_state'], 'INACTIVE')
        self.assertEqual(overlay['routes']['padataset:scientific-single-gpu-2']['admission_state'], 'DISABLED')

    def test_lane_b_preserves_same_scientific_semantics(self):
        contracts = load('architecture/lambda-ci-execution-contracts.v1.json')['contracts']
        a = dict(contracts['scientific-single-gpu-v1'])
        b = dict(contracts['scientific-single-gpu-2-v1'])
        a.pop('resource_class')
        b.pop('resource_class')
        a.pop('execution_profile')
        b.pop('execution_profile')
        a.pop('lifecycle')
        b.pop('lifecycle')
        self.assertEqual(a, b)

if __name__ == '__main__':
    unittest.main()
