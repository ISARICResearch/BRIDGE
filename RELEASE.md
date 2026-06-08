# Release Guidelines

BRIDGE (GitHub) releases should be based on [semantic versioning](https://semver.org), where each release is assigned a three-part version number, stored in the `__version__` attribute in the `bridge/__init__.py` file, in the format `<MAJOR VERSION>.<MINOR VERSION>.<PATCH NUMBER>` where:

- `<MAJOR VERSION>` - incremented if there are breaking (public) API changes
- `<MINOR VERSION>` - incremented if the changes are non-breaking and backwards compatible, e.g. refactoring of existing functionality, non-breaking addition or modifications of functionality
- `<PATCH NUMBER>` - incremented for bug fixes

> [!Note]
The version number should **NOT** be prefixed with the letter `"v"` (or `"V"`), as that should be used only for Git tags corresponding to releases.

The release process is not currently automated (there is no GitHub release workflow), and releases are created manually from the `main` branch, which also triggers [Zenodo](https://zenodo.org/) releases. This may change in the future, but for the present the current release process can be continued. However to ensure consistency, a logically ordered sequence of steps should be followed:

1. Check that the new release version number is present in the `bridge/__init__.py` file (this is the value of the `__version__` attribute in that file), and that it conforms to the semantic versioning scheme as described above. If these conditions aren't met then this can be done in a release PR based on a release branch created from `main`, and the release done as usual after the PR is merged into `main`.

2. Create the release on GitHub: Releases → Draft a new release, while ensuring that

   - the release title follows the convention `v<semantic version number>`, e.g. `v1.3.0`, and **don't** include the repository or package name
   - a Git tag matching `v<semantic version number>` is created
   - `main` is set as the target branch for the release
   - the release label is set to `"Latest"`

The Release notes option can be used to automatically generate release notes, and can be very useful. Release binaries or other artifacts such as Python wheels (in `.whl` file format) are optional.

3. Publish the release.
