from pathlib import Path
from faf28_workflows import wrap_faf_analysis_step_as_task, FafStepResult
from faf_classes.faf_analysis import FafAnalysis

# Mock FafAnalysis class for testing
class MockFafAnalysis(FafAnalysis):
    def __init__(self, internal_kwargs: dict | None = None):
        super().__init__(internal_kwargs=internal_kwargs)

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        return []

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        return "mock_output.png"
        
    def run(self):
        # Override run to simulate behavior we just implemented
        # In the real class, run() calls single_image_job via map/list comp
        # Here we just return a list mimicking the new behavior
        if self.internal_kwargs and self.internal_kwargs.get('fail'):
            return ["failed with error"]
        return ["mock_output.png"]

def test_wrapper_success():
    print("Testing wrapper success case...")
    task = wrap_faf_analysis_step_as_task(MockFafAnalysis, task_name="test_task")
    result = task.fn(i="some_input") # call the underlying function directly to avoid prefect context need if possible, or we might need to mock get_run_logger
    
    # If calling .fn fails due to get_run_logger, we might need to mock it.
    # But let's see if we can run it.
    # Actually, get_run_logger() will fail if not in a flow/task.
    # So we'll mock get_run_logger.
    
    print(f"Result type: {type(result)}")
    print(f"Result success: {result.success}")
    print(f"Result output: {result.output}")
    
    assert isinstance(result, FafStepResult)
    assert result.success is True
    assert result.output == ["mock_output.png"]
    print("Success case passed!")

def test_wrapper_failure():
    print("\nTesting wrapper failure case...")
    task = wrap_faf_analysis_step_as_task(MockFafAnalysis, task_name="test_fail_task")
    result = task.fn(fail=True)
    
    print(f"Result type: {type(result)}")
    print(f"Result success: {result.success}")
    print(f"Result error: {result.error}")
    
    assert isinstance(result, FafStepResult)
    assert result.success is False
    assert "failed" in result.error
    print("Failure case passed!")

if __name__ == "__main__":
    # Mocking get_run_logger since we are running outside of Prefect flow
    from unittest.mock import MagicMock
    import prefect
    prefect.get_run_logger = MagicMock()
    
    test_wrapper_success()
    test_wrapper_failure()
