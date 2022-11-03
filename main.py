import json
import urllib.parse
import urllib.request

DEBUG = False

INITIAL_LINK = "https://e0f5e8673c64491d8cce34f5.z35.web.core.windows.net/treasure.json"
MONIES = {
    "sapphire": 200,
    "ruby": 250,
    "diamond": 400
}
USED_LINKS = []


def log(*args, ignore=False, **kwargs):
    if DEBUG or ignore:
        print(*args, **kwargs)


def is_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def contains_url(string):
    if "http" in string:
        parts = string.split(" ")
        for part in parts:
            if is_url(part):
                return part

    return None


def most_common(lst):
    return max(set(lst), key=lst.count)


class TreasureTraverser:
    def __init__(self, link):
        self.link = link

        USED_LINKS.append(link)

        self.child_traverser = []

        self._JSON = None

        self.stats = {
            "dubloons": 0,
            "dead spiders": 0,
            "holy grail": '',
            "boot sizes": []
        }

        self.total_stats = {}

        self._current_location = None

    def getJSON(self):
        with urllib.request.urlopen(self.link) as url:
            self._JSON = json.load(url)

    def collate_stats(self):
        self.total_stats = self.stats

        for child in self.child_traverser:
            self.total_stats = {k: self.total_stats.get(k, 0) + child.total_stats.get(k, 0)
                                for k in set(self.total_stats) | set(child.total_stats)}

    def start(self):
        self.getJSON()

        self.search_list(self._JSON)

        self.collate_stats()

    def handle_element(self, element):
        if type(element) == str:
            log(element)

            if element == "holy-grail":
                self.stats["holy grail"] = self._current_location

            url = contains_url(element)
            if url is not None:
                log("LINK: " + url)
                self.found_link(url)

        elif type(element) == dict:
            self.search_dict(element)
        elif type(element) == list:
            self.search_list(element)
        else:
            log(str(type(element)) + ": " + str(element))
            pass

    def search_list(self, lst):
        for element in lst:
            self.handle_element(element)

    def search_dict(self, dct):
        if "location" in dct:
            self._current_location = dct["location"]

        for key, val in dct.items():
            log(key + ": " + str(val))

            # Check for money
            if key == "holy-grail":
                self.stats["holy grail"] = self._current_location
            elif type(val) == dict:
                if key in MONIES and "count" in val:
                    self.stats["dubloons"] += val["count"] * MONIES[key]
                elif "value" in val:
                    if type(val["value"]) == int:
                        self.stats["dubloons"] += val["value"]
                    else:
                        self.handle_element(val)
                elif key == "spider":
                    if "alive" in val:
                        if not val["alive"]:
                            self.stats["dead spiders"] += 1
                elif key == "boots":
                    if "size" in val:
                        self.stats["boot sizes"].append(val["size"])

                    # Handle anyway, cause there may be notes
                    self.handle_element(val)
                else:
                    self.handle_element(val)
            else:
                self.handle_element(val)

    def found_link(self, link):
        # Prevent links being duplicated
        if link not in USED_LINKS:
            new = TreasureTraverser(link)
            self.child_traverser.append(new)
            new.start()


def main():
    start = TreasureTraverser(INITIAL_LINK)
    start.start()

    print(f"Holy Grail location: {start.total_stats['holy grail']}")
    print(f"{start.total_stats['dubloons']} Doubloons")
    print(f"{start.total_stats['dead spiders']} Dead spiders")
    print(f"{most_common(start.total_stats['boot sizes'])} is the average boot size")


if __name__ == "__main__":
    main()
