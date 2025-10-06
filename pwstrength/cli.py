#!/usr/bin/env python3
import argparse, json
from getpass import getpass
from .meter import estimate

def main():
    p = argparse.ArgumentParser(description="Password Strength Meter - estimates entropy and flags patterns (repeats, dates, l33t).")
    p.add_argument("password", nargs="?", help="Password to evaluate. If omitted, you will be prompted (hidden).")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("--show", action="store_true", help="Echo the password back in text output (hidden by default).")
    args = p.parse_args()
    pw = args.password or getpass("Enter password: ")
    res = estimate(pw)
    if args.json:
        obj = {
            "length": res.length,
            "categories": res.categories,
            "base_entropy_bits": res.base_entropy_bits,
            "adjusted_entropy_bits": res.adjusted_entropy_bits,
            "guesses": res.guesses,
            "score": res.score,
            "flags": [{"type":f.type,"span":list(f.span),"detail":f.detail} for f in res.flags],
            "feedback": res.feedback
        }
        print(json.dumps(obj, indent=2))
    else:
        if args.show:
            print(f"Password : {res.password}")
        print(f"Length   : {res.length}")
        print(f"Classes  : {', '.join(res.categories) or '-'}")
        print(f"Entropy  : {res.adjusted_entropy_bits} bits (base {res.base_entropy_bits})")
        print(f"Score    : {res.score} / 4")
        if res.flags:
            print("Flags    :")
            for fl in res.flags:
                s,e = fl.span
                print(f"  - {fl.type:<13} [{s}:{e}]  {fl.detail}")
        else:
            print("Flags    : -")
        if res.feedback:
            print("Feedback :")
            for tip in res.feedback:
                print(f"  * {tip}")

if __name__ == "__main__":
    main()
