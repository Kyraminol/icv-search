from argparse import ArgumentParser
from json import dump
from pprint import pprint
from os import startfile
from icv import ICV
import config


def main():
    parser = ArgumentParser(description="Search and download ICV from CLI", add_help=False)
    parser.add_argument("--search", "-s",
                        help="Filter releases by text")
    parser.add_argument("--category", "-c", nargs="*",
                        help="Category filter, leave blank to just list all categories."
                             " Can be multiple items (-c CATEGORY1 CATEGORY2 CATEGORY3)")
    parser.add_argument("--output", "-o", action="store_true",
                        help="Output results to file")
    parser.add_argument("--limit", "-l",
                        help="Number of search results for each category (default: 5 if all, 10 otherwise)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Select releases to download after search, works only with --search/-s")
    parser.add_argument("--download", "-d", action="store_true",
                        help="Download magnets directly with default client, works only with --interactive/-i")
    parser.add_argument("--withdraw", "-w", action="store_true",
                        help="Withdraw like after download, works only with --interactive/-i")
    parser.add_argument("--help", "-h", action="help", help="Show this message and exits immediately")
    args = parser.parse_args()

    icv = ICV(config)

    if args.category is not None:
        if len(args.category) == 0:
            for category in icv.get_category_list():
                print(category)
            exit(0)
        if "all" in args.category:
            args.category = None
            if args.limit is None:
                args.limit = 5
        else:
            if args.limit is None:
                args.limit = 10

    print("Loading releases (can take a while)...")
    results = icv.get_releases(args.category)

    if args.search and results:
        print("Searching text in releases...")
        results = icv.search(args.search, results, int(args.limit))
        if args.interactive:
            i = 0
            items = []
            for key, value in results.items():
                print("{}:".format(key))
                for item in value:
                    i += 1
                    items.append(item + (key, ))
                    print("{}) {}".format(i, item[0]))
            indexes = input("Numbers to download, comma separated (e.g.: 1, 2, 4): ")
            results = [items[int(x) - 1] for x in indexes.split(",")]

    output = []
    if args.search and args.interactive:
        for name, _, thread_id, category in results:
            print("Loading magnets for {}...".format(name))
            output.append({
                "name": name,
                "thread": "https://www.icv-crew.com/forum/index.php?topic={}".format(thread_id),
                "magnets": icv.get_magnets(thread_id, args.withdraw),
                "category": category,
            })
    elif args.search:
        for key, value in results.items():
            for name, _, thread_id in value:
                output.append({
                    "name": name,
                    "thread": "https://www.icv-crew.com/forum/index.php?topic={}".format(thread_id),
                    "magnets": None,
                    "category": key,
                })
    else:
        for key, value in results.items():
            for thread_id, name in value.items():
                output.append({
                    "name": name,
                    "thread": "https://www.icv-crew.com/forum/index.php?topic={}".format(thread_id),
                    "magnets": None,
                    "category": key,
                })

    if args.output and output:
        with open("output.json", "w+") as file:
            dump(output, file, indent=2)
    elif not args.output and output:
        pprint(output)

    if args.download and args.interactive and output:
        print("Opening all magnets with default client...")
        for release in output:
            for magnet in release["magnets"]:
                startfile(magnet)

    if not output:
        print("No results")


if __name__ == '__main__':
    main()
