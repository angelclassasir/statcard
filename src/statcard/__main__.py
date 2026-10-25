"""Command line interface for statcard."""

import argparse
import asyncio
import sys

from statcard import __version__
from statcard.providers.valorant import (
    VALID_REGIONS,
    ValorantProviderError,
    fetch_valorant_stats,
)
from statcard.render import save_card


def build_parser() -> argparse.ArgumentParser:
    """Define the CLI: one subcommand per supported game."""
    parser = argparse.ArgumentParser(
        prog="statcard",
        description="Generate visual stat cards for your favorite FPS games.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="game", required=True)

    valorant = subparsers.add_parser("valorant", help="Generate a Valorant stat card")
    valorant.add_argument("riot_id", help='Riot ID, e.g. "Name#TAG"')
    valorant.add_argument(
        "--region",
        default="eu",
        choices=VALID_REGIONS,
        metavar="REGION",
        help="Riot region: eu, na, ap, kr, br, latam (default: eu)",
    )
    valorant.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the disk cache and force a fresh API fetch",
    )
    valorant.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Output PNG path (default: output/valorant_card.png)",
    )
    return parser


def main() -> int:
    """CLI entry point. Returns the process exit code."""
    args = build_parser().parse_args()

    if args.game == "valorant":
        name, sep, tag = args.riot_id.partition("#")
        if not sep or not name.strip() or not tag.strip():
            print('Error: the Riot ID must look like "Name#TAG".', file=sys.stderr)
            return 1
        try:
            stats = asyncio.run(
                fetch_valorant_stats(
                    name.strip(),
                    tag.strip(),
                    region=args.region,
                    use_cache=not args.no_cache,
                )
            )
        except ValorantProviderError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        path = save_card(stats, path=args.output)
        print(f"Card saved to: {path}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
