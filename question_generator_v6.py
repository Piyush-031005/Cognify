# DEPRECATED: Use question_generator.py instead
# This file is preserved only for historical reference as requested by the supervisor.
# Capabilities have been fully merged into the production question_generator.py.

from question_generator import run_generator, generate_question

if __name__ == "__main__":
    import sys
    print("WARNING: This generator file (v6) is deprecated. Redirecting execution to production question_generator.py...")
    run_generator()