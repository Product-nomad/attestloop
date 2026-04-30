"""Allow `python -m attestloop ...` as a shorter alternative to
`python -m attestloop.pipeline ...`. Pure passthrough."""
import sys

from attestloop.pipeline import main

if __name__ == "__main__":
    sys.exit(main())
