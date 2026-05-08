# findus-glitcherbench

This repository is a modified fork of the `findus` hardware glitching library.

The fork contains changes required for integration with the GlitcherBench thesis project and preserves the hardware-control environment used during the experiments.

## Origin

This repository is based on the original `findus` project.

Original project:

```text
https://github.com/MKesenheimer/fault-injection-library

```

This fork keeps the original GPLv3 licensing terms.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/YOUR_USERNAME/findus-glitcherbench.git@v0.1.0-glitcherbench
```

For development:

```bash
git clone https://github.com/YOUR_USERNAME/findus-glitcherbench.git
cd findus-glitcherbench
pip install -e .
```

## Usage with GlitcherBench

This fork is intended to be used as a hardware backend for:

```text
https://github.com/K3fas/glitcherbench
```

## Syncing with upstream

If needed, add the original project as an upstream remote:

```bash
git remote add upstream https://github.com/MKesenheimer/fault-injection-library
git fetch upstream
```

## License

This repository is licensed under GPLv3, following the license of the original `findus` project.

Modifications in this fork are also distributed under GPLv3.

See `LICENSE` for details.

## Modification notice

This fork was modified for use with the GlitcherBench thesis project.

Author of modifications: `Peter Bránecký `  
Related project: `https://github.com/K3fas/glitcherbench`  
Version used in thesis: `v1.0.0-glitcherbench`
