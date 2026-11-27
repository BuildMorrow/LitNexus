"""Tests for Sprint F: Isolated Python Code Sandbox Security & Execution."""

import pytest

from app.services.code_sandbox import code_sandbox, validate_python_code


@pytest.mark.parametrize(
    "unsafe_code",
    [
        "import os\nprint(os.listdir('.'))",
        "import subprocess\nsubprocess.run(['ls'])",
        "open('/etc/passwd').read()",
        "__import__('sys').exit(1)",
        "x = ().__class__.__base__.__subclasses__()",
    ],
)
def test_sandbox_blocks_unsafe_operations(unsafe_code: str):
    err = validate_python_code(unsafe_code)
    assert err is not None


async def test_sandbox_executes_pandas_scipy_and_captures_matplotlib():
    csv_data = (
        "patient_id,f1_score,noise\n"
        "p1,0.98,low\n"
        "p2,0.97,low\n"
        "p3,0.86,high\n"
        "p4,0.84,high\n"
    )
    code = """```python
low = df[df['noise'] == 'low']['f1_score']
high = df[df['noise'] == 'high']['f1_score']
u_stat, p_val = stats.mannwhitneyu(low, high)
print(f"N={len(df)}, U={u_stat:.2f}, p={p_val:.4f}")

fig, ax = plt.subplots()
ax.boxplot([low, high], tick_labels=['Low', 'High'])
ax.set_title('F1 under Noise')
```"""
    res = await code_sandbox.execute_code_async(code=code, csv_text=csv_data, timeout_seconds=10.0)
    assert res.success is True
    assert res.error is None
    assert "N=4, U=" in res.stdout
    assert len(res.figures) == 1
    assert len(res.figures[0]) > 100
