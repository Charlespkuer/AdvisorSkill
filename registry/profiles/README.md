# Profile registry

Paths use two levels, `<discipline>/<advisor>`. For example, [`phy/sxz`](phy/sxz/) reserves a category. Its empty `.gitkeep` keeps the folder in Git.

Store local evidence in `.advisorskill/<discipline>/<advisor>/` or in an explicitly selected private directory outside the repository. A local profile is ready for import once `advisorskill init` creates its `state.json`. The [demo fixtures](../../tests/fixtures/) contain synthetic feedback.

Public profiles require explicit authorization, a declared license, and manual review. The public export and withdrawal workflow is scheduled for M3.
