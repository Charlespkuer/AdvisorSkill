# Submit a public writing guide

1. Ask the author which active rules they want to share, which public discipline and advisor alias to use, and which license they authorize. Run `advisorskill export-public --workspace PATH --discipline phy --advisor sxz --license CC-BY-4.0 --rule R-001` with their choices.
2. Show the exact resulting `public-draft/phy/sxz/GUIDE.md`. Check rule wording, scope, and exceptions for identities, project details, private excerpts, source paths, or credentials. Edit the draft where needed and ask the author to approve the resulting text and repository. Keep the private state and build files local.
3. Run `advisorskill submit-guide --guide FILE --repo Charlespkuer/AdvisorSkill` for the current document digest. After the author approves this exact version and destination, pass that digest using `--approve SHA256`. Return the Issue link on success. If GitHub does not confirm the post, check for the issue before retrying.
