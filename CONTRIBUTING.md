# Contributing

Use a local virtual environment with `python -m pip install -e ".[test]"`. Run `python -m pytest` and `python scripts/demo.py` with synthetic input. Regenerate protocol schemas with `python scripts/generate_schemas.py` after model changes.

## Contributing advisor preferences

Use a path such as `phy/sxz` to identify a profile. For public submissions, describe a proposed preference in your own words, when it applies, any exceptions, and a synthetic example. Use a public alias and include the scope of authorization and the proposed license. Keep raw comments, manuscript excerpts, and institutional identities private unless the relevant rightsholders have authorized disclosure.

A low-friction GitHub workflow starts with a structured Issue form. A maintainer can convert reviewed submissions into a registry change and open the pull request. At higher volume, a workflow can generate a draft pull request after maintainer triage. Use CI to validate its schema and keep merge approval with the maintainer. [GitHub Issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository) · [Profile registry](registry/profiles/README.md)
