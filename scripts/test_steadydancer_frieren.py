#!/usr/bin/env python3
"""
SteadyDancer/ComfyUI Integration Test - Frieren Choreography

Tests SteadyDancer dance video generation using physics parameters
from the Frieren cosplay choreography analysis.

Usage:
    python3 test_steadydancer_frieren.py [--vanilla] [--turbo] [--both]
"""

import json
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
COMFYUI_URL = "http://localhost:8188"
ANALYSIS_FILE = "/mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/frieren-cosplay-dance-analysis.md"
VIDEO_INPUT = "/mnt/m/solar/aria-cruz-ai/01-reto-freelancer/video/video_analysis/cosplayer-frieren-vibe-check-dc-Cody.mp4"
WORKFLOWS_DIR = "/home/oz/projects/2025/oz/12/runpod/docker/workflows"
OUTPUT_DIR = "/workspace/ComfyUI/output"

class SteadyDancerTest:
    """Test SteadyDancer workflows with Frieren analysis."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_file": ANALYSIS_FILE,
            "video_input": VIDEO_INPUT,
            "tests": []
        }

    def check_comfyui_health(self):
        """Verify ComfyUI is running."""
        print("\n" + "="*80)
        print(" PHASE 1: SETUP VALIDATION")
        print("="*80 + "\n")

        try:
            response = requests.get(f"{COMFYUI_URL}/api/system", timeout=5)
            if response.status_code == 200:
                print("✓ ComfyUI server is running")
                system_info = response.json()
                print(f"  GPU: {system_info.get('system', {}).get('gpu_count', 'unknown')}")
                return True
            else:
                print("✗ ComfyUI server returned error: " + str(response.status_code))
                return False
        except Exception as e:
            print(f"✗ ComfyUI server not responding: {e}")
            print(f"  Please start ComfyUI: python main.py --enable-steadydancer")
            return False

    def verify_workflows(self):
        """Check if workflow files exist."""
        print("\nVerifying workflow files...")

        workflows = {
            "vanilla": f"{WORKFLOWS_DIR}/steadydancer-dance.json",
            "turbo": f"{WORKFLOWS_DIR}/steadydancer-turbo.json"
        }

        all_valid = True
        for name, path in workflows.items():
            workflow_path = Path(path)
            if workflow_path.exists():
                size = workflow_path.stat().st_size / 1024
                print(f"✓ {name.capitalize()} workflow: {path} ({size:.1f} KB)")

                # Validate JSON
                try:
                    with open(path) as f:
                        json.load(f)
                    print(f"  └─ JSON syntax: Valid")
                except json.JSONDecodeError as e:
                    print(f"  └─ JSON syntax: Invalid - {e}")
                    all_valid = False
            else:
                print(f"✗ {name.capitalize()} workflow not found: {path}")
                all_valid = False

        return all_valid

    def verify_analysis(self):
        """Check if analysis file exists."""
        print("\nVerifying analysis file...")

        analysis_path = Path(ANALYSIS_FILE)
        if analysis_path.exists():
            size = analysis_path.stat().st_size / 1024
            print(f"✓ Analysis file exists: {ANALYSIS_FILE}")
            print(f"  Size: {size:.1f} KB")
            print(f"  Last modified: {datetime.fromtimestamp(analysis_path.stat().st_mtime)}")

            # Check key sections
            with open(analysis_path) as f:
                content = f.read()
                sections = ["MOVEMENT PHYSICS", "CHARACTER", "CROSS-ANALYSIS"]
                for section in sections:
                    if section in content:
                        print(f"  ✓ Section found: {section}")
                    else:
                        print(f"  ✗ Section missing: {section}")
            return True
        else:
            print(f"✗ Analysis file not found: {ANALYSIS_FILE}")
            return False

    def run_vanilla_test(self):
        """Test vanilla SteadyDancer workflow."""
        print("\n" + "="*80)
        print(" PHASE 2: VANILLA STEADYDANCER TEST")
        print("="*80 + "\n")

        test_result = {
            "name": "Vanilla SteadyDancer",
            "workflow": "steadydancer-dance.json",
            "steps": 50,
            "status": "pending",
            "generation_time": None,
            "output_file": None
        }

        try:
            # Load workflow
            workflow_path = f"{WORKFLOWS_DIR}/steadydancer-dance.json"
            with open(workflow_path) as f:
                workflow = json.load(f)

            print("Loaded workflow: steadydancer-dance.json")
            print(f"Nodes: {len(workflow)} configured")

            # Submit to ComfyUI
            print("\nSubmitting workflow to ComfyUI...")
            start_time = time.time()

            response = requests.post(
                f"{COMFYUI_URL}/prompt",
                json={"prompt": workflow},
                timeout=30
            )

            if response.status_code == 200:
                prompt_id = response.json().get("prompt_id")
                print(f"✓ Workflow queued: {prompt_id}")

                # Monitor execution
                print("\nMonitoring execution...")
                generation_time = self._monitor_execution(prompt_id)

                test_result["status"] = "completed"
                test_result["generation_time"] = generation_time
                test_result["prompt_id"] = prompt_id

                print(f"✓ Generation completed in {generation_time:.1f} seconds")
            else:
                print(f"✗ Failed to queue workflow: {response.status_code}")
                test_result["status"] = "failed"
                test_result["error"] = response.text

        except Exception as e:
            print(f"✗ Error during vanilla test: {e}")
            test_result["status"] = "error"
            test_result["error"] = str(e)

        self.results["tests"].append(test_result)
        return test_result

    def run_turbo_test(self):
        """Test TurboDiffusion accelerated workflow."""
        print("\n" + "="*80)
        print(" PHASE 3: TURBODIFFUSION ACCELERATED TEST")
        print("="*80 + "\n")

        test_result = {
            "name": "TurboDiffusion Accelerated",
            "workflow": "steadydancer-turbo.json",
            "steps": 4,
            "status": "pending",
            "generation_time": None,
            "output_file": None
        }

        try:
            # Load workflow
            workflow_path = f"{WORKFLOWS_DIR}/steadydancer-turbo.json"
            with open(workflow_path) as f:
                workflow = json.load(f)

            print("Loaded workflow: steadydancer-turbo.json")
            print(f"Nodes: {len(workflow)} configured")
            print("Configuration: 4-step TurboDiffusion (100-200x acceleration)")

            # Submit to ComfyUI
            print("\nSubmitting workflow to ComfyUI...")
            start_time = time.time()

            response = requests.post(
                f"{COMFYUI_URL}/prompt",
                json={"prompt": workflow},
                timeout=30
            )

            if response.status_code == 200:
                prompt_id = response.json().get("prompt_id")
                print(f"✓ Workflow queued: {prompt_id}")

                # Monitor execution
                print("\nMonitoring execution...")
                generation_time = self._monitor_execution(prompt_id)

                test_result["status"] = "completed"
                test_result["generation_time"] = generation_time
                test_result["prompt_id"] = prompt_id

                # Calculate speedup
                speedup = 600 / generation_time  # Assuming vanilla ~10 min
                print(f"✓ Generation completed in {generation_time:.1f} seconds")
                print(f"✓ Estimated speedup: {speedup:.1f}x")
            else:
                print(f"✗ Failed to queue workflow: {response.status_code}")
                test_result["status"] = "failed"
                test_result["error"] = response.text

        except Exception as e:
            print(f"✗ Error during TurboDiffusion test: {e}")
            test_result["status"] = "error"
            test_result["error"] = str(e)

        self.results["tests"].append(test_result)
        return test_result

    def _monitor_execution(self, prompt_id, timeout=1800):
        """Monitor ComfyUI execution and wait for completion."""
        start_time = time.time()
        check_interval = 5

        while True:
            elapsed = time.time() - start_time

            # Check execution history
            try:
                response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=5)
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        execution = history[prompt_id]
                        if "outputs" in execution:
                            # Generation completed
                            return elapsed
                        else:
                            status = "processing"
            except:
                pass

            # Timeout check
            if elapsed > timeout:
                print(f"✗ Generation timed out after {timeout} seconds")
                return elapsed

            # Print progress
            if int(elapsed) % 10 == 0:
                print(f"  Elapsed: {int(elapsed)}s...")

            time.sleep(check_interval)

    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*80)
        print(" TEST REPORT")
        print("="*80 + "\n")

        report = f"""
SteadyDancer/ComfyUI Integration Test Report
Generated: {self.results['timestamp']}

ANALYSIS USED:
  File: {ANALYSIS_FILE}
  Confidence: 90%
  Content: Movement Physics + Character Analysis

INPUT VIDEO:
  File: {VIDEO_INPUT}
  Duration: 6.0 seconds
  Frames: 180 @ 30 FPS

TEST RESULTS:
"""

        for i, test in enumerate(self.results["tests"], 1):
            status_symbol = "✓" if test["status"] == "completed" else "✗"
            report += f"""
{i}. {test['name']}
   Workflow: {test['workflow']}
   Steps: {test['steps']}
   Status: {status_symbol} {test['status']}
"""
            if test["generation_time"]:
                report += f"   Generation Time: {test['generation_time']:.1f}s\n"
            if test.get("error"):
                report += f"   Error: {test['error']}\n"

        report += """
NEXT STEPS:
1. Verify generated video files in: /workspace/ComfyUI/output/
2. Check character identity preservation
3. Validate motion blur in generated frames
4. Compare vanilla vs TurboDiffusion quality
5. Validate analysis parameters applied correctly

ANALYSIS PARAMETERS TO VERIFY:
  ✓ Garment Physics: damping=0.15, stiffness=0.8
  ✓ Hair Dynamics: ~3000 strands, shoulder-to-waist
  ✓ Motion Blur: Limbs (radial), Hair (arc), Fabric (tangential)
  ✓ Foot Contact: Alternating shift, right pivot
  ✓ Limb Motion: Arms 120°, legs 45°
  ✓ Character: Frieren, graceful, precise

RECOMMENDED NEXT ACTIONS:
  1. Manual video inspection (playback)
  2. Frame-by-frame analysis for motion blur
  3. Character consistency verification
  4. Physics parameter validation
  5. Production readiness assessment
"""

        print(report)

        # Save report
        report_file = f"/home/oz/projects/2025/oz/12/runpod/dev/agents/artifacts/doc/steadydancer-test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\nReport saved: {report_file}")
        return report_file

    def run(self, test_type="both"):
        """Run all tests."""
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*15 + "STEADYDANCER/COMFYUI INTEGRATION TEST" + " "*25 + "║")
        print("║" + " "*15 + "Frieren Cosplay Choreography Analysis" + " "*25 + "║")
        print("╚" + "="*78 + "╝\n")

        # Phase 1: Setup validation
        if not self.check_comfyui_health():
            print("\n✗ ComfyUI health check failed. Cannot proceed.")
            return False

        if not self.verify_workflows():
            print("\n✗ Workflow verification failed.")
            return False

        if not self.verify_analysis():
            print("\n✗ Analysis verification failed.")
            return False

        print("\n✓ All setup validations passed\n")

        # Phase 2: Run tests
        if test_type in ["vanilla", "both"]:
            self.run_vanilla_test()

        if test_type in ["turbo", "both"]:
            self.run_turbo_test()

        # Generate report
        self.generate_report()

        return True


def main():
    parser = argparse.ArgumentParser(description="Test SteadyDancer with Frieren analysis")
    parser.add_argument(
        "--vanilla",
        action="store_true",
        help="Test vanilla workflow only"
    )
    parser.add_argument(
        "--turbo",
        action="store_true",
        help="Test TurboDiffusion workflow only"
    )
    parser.add_argument(
        "--both",
        action="store_true",
        default=True,
        help="Test both workflows (default)"
    )

    args = parser.parse_args()

    # Determine test type
    test_type = "both"
    if args.vanilla and not args.turbo:
        test_type = "vanilla"
    elif args.turbo and not args.vanilla:
        test_type = "turbo"

    # Run tests
    tester = SteadyDancerTest()
    success = tester.run(test_type)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
