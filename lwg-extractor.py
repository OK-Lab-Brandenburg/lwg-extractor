import camelot
import json
import requests
import argparse
import logging
from os import remove
from pathlib import Path
from bs4 import BeautifulSoup as bs

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("LWG")

BASE_URL = "https://lausitzer-wasser.de/de/kundenportal/trinkwasser/wasserqualitaet-wasserhaerte.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='LWG PDF data extractor')
    parser.add_argument('output', help='Output file name')
    return parser.parse_args()


def extract_href_title(href: str) -> str:
    """
    Extract name of Wasserwerk from href title

    :param: href title
    :return: parsed title
    """
    href = href.strip()
    split = href.split("–", 1)
    if len(split) == 2:
        split = split[-1].split("(", 1)
        if len(split) == 2:
            return split[0].strip()
    else:
        log.error("Wrong href title: %s", href)

def extract_pdf_urls(base_site):
    """
    Extract all links of Wasserwerke from LWG website

    :param: base_site beutifulsoup site
    :return: array of tuple(titel, link)
    """
    resp = requests.get(base_site)
    if resp:
        site = bs(resp.text, features="html.parser")
        html_links = site.find("div", class_="boxWrap downloads")
        links = html_links.find_all("a", class_="hasImg")
        result = []
        for l in links:
            title = extract_href_title(l.getText())
            if title:
                link = l["href"]
                result.append((title, link))
        return result
    else:
        log.error("Can't request site %s", base_site)


def parse_numbers(num: str):
    """
    Parse number of typ int and float
    """
    # replace german decimal comma with dot
    num = num.replace(",", ".", 1)
    result_num = None
    try:
        result_num = int(num)
    except ValueError:
        try:
            result_num = float(num)
        except ValueError:
            log.debug("Can't convert %s to numerical type", num)
    return result_num
        

def make_dict(raw_values: list) -> dict:
    """
    Create key-value map with raw_values
    """
    data = {}
    if len(raw_values) == 8:
        data["haerte"] = parse_numbers(raw_values[0])
        data["calcium"] = parse_numbers(raw_values[1])
        data["magnesium"] = parse_numbers(raw_values[2])
        data["natrium"] = parse_numbers(raw_values[3])
        data["kalium"] = parse_numbers(raw_values[4])
        data["chlorid"] = parse_numbers(raw_values[5])
        data["nitrat"] = parse_numbers(raw_values[6])
        data["sulfit"] = parse_numbers(raw_values[7])
    else:
        log.error("Can't handle input data")
    return data


def extract_pdf_data(pdf: str) -> dict:
    """
    Extract needed data from pdf
    """
    tables = camelot.read_pdf(pdf)
    if tables:
        log.info("Read data from file: %s", pdf)
        df = tables[0].df
        values = []
        for r in df.iterrows():
            if int(r[0]) in [2, 11, 12, 13, 14, 15, 16, 17]:
                values.append(r[1][4])
        return make_dict(values)
    else:
        log.debug("Upps error!")


def load_pdf_extract_content(data: tuple) -> dict:
    """
    Load PDF from link and extract data

    :return: dict with parsed content
    """
    tmp_file = 'tmp.pdf'
    result = {}
    for d in data:
        log.info("Download file from %s", d[1])
        resp = requests.get(d[1])
        if resp:
            # create tmp file
            filename = Path(tmp_file)
            filename.write_bytes(resp.content)
            values = extract_pdf_data(tmp_file)
            result[d[0]] = values
            log.debug("PDF Content: %s", values)
            # remove tmp file
            remove(tmp_file)
        else:
            log.error("Can't download %s from %s", d[0], d[1])
    return result


def main():
    args = parse_args()
    if args:
        links = extract_pdf_urls(BASE_URL)
        log.info("Found %s links on page %s", len(links), BASE_URL)
        data = load_pdf_extract_content(links)
        log.info("Extracted data: %s", data)
        if data:
            with open(args.output, 'w') as fp:
                json.dump(data, fp)
            log.info("Extracted data written to %s", args.output)
        else:
            log.error("No data found")


main()

