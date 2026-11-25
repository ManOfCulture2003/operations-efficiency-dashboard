from unittest.mock import patch

import pytest
from matplotlib.figure import Figure
import operations_efficiency_dashboard as app


@pytest.mark.parametrize('stage', ['layout', 'save'])
def test_failed_chart_releases_figure_and_allows_retry(tmp_path, stage):
    summary = app.summarize(app.validate_data(app.generate_data(days=1)))
    existing = set(app.plt.get_fignums())
    method = 'tight_layout' if stage == 'layout' else 'savefig'
    with patch.object(Figure, method, side_effect=OSError('simulated output failure')):
        with pytest.raises(OSError, match='simulated'):
            app.save_chart(summary, tmp_path / 'failed.png', 'DelayIncidencePct', 'Delayed (%)')
    assert set(app.plt.get_fignums()) == existing
    app.save_chart(summary, tmp_path / 'retry.png', 'DelayIncidencePct', 'Delayed (%)')
    assert (tmp_path / 'retry.png').stat().st_size > 0
    assert set(app.plt.get_fignums()) == existing
