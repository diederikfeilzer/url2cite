#!/usr/bin/env python3

import sys, requests, re
from bs4 import BeautifulSoup
from urllib.parse import unquote
from itertools import groupby

def isdoi(doi):
	return not not re.compile("10.\d{4,9}/[-._;()/:A-Za-z0-9]+").match(doi)

def get_doi_from_url(url):

	candidates = []

	# get html

	headers = {
	   'cache-control': 'max-age=0',
	   'sec-ch-ua': 'Google Chrome 79',
	   'upgrade-insecure-requests': '1',
	   'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
	   'sec-fetch-dest': 'document',
	   'sec-fetch-user': '?1',
	   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	   'sec-origin-policy': '0',
	   'sec-fetch-site': 'none',
	   'sec-fetch-mode': 'navigate',
	   'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
	}

	response = requests.get(url, headers=headers)
	
	soup = BeautifulSoup(response.content, 'html.parser')

	# check citation_doi meta tag

	tags = soup.select('meta[name="citation_doi"][content]')

	for tag in tags:
		
		evl = tag["content"]

		if isdoi(evl):
			candidates.append((evl, "citation_doi", 1))

	# check citation_doi meta tag

	tags = soup.select('meta[name="evt-doiPage"][content]')

	for tag in tags:
		
		evl = tag["content"]

		if isdoi(evl):
			candidates.append((evl, "evt-doiPage", 1))

	# check dc.Identifier meta tag

	tags = soup.select('meta[name="dc.Identifier"][content]')

	for tag in tags:
		
		evl = tag["content"]

		if isdoi(evl):
			candidates.append((evl, "dc.Identifier", 0.9))

	# pbContext

	tags = soup.select('meta[name="pbContext"][content]')
	
	for tag in tags:

		pbContext = unquote(tag["content"])

		regex = r"article:article:doi\\:(10.\d{4,9}/[-._()/:A-Z0-9]+);"
	
		matches = re.search(regex, pbContext, re.MULTILINE | re.IGNORECASE)
	
		if matches:

			evl = str(matches.group(1))

			if isdoi(evl):
				candidates.append((evl, "pbContext", 0.8))

	# doi: doi link or doi
	
	regex = r"(?:DOI: +)(?:(?:https?:\/\/)?doi.org\/)?(10.\d{4,9}/[-._()/:A-Z0-9]+)"
	
	matches = re.finditer(regex, str(response.content), re.MULTILINE | re.IGNORECASE)
	
	for match in matches:

		evl = str(match.group(1))

		if isdoi(evl):
			candidates.append((evl, "doi: text", 0.2))

	# any doi link
	
	regex = r"(?:(?:https?:\/\/)?doi.org\/)?(10.\d{4,9}/[-._()/:A-Z0-9]+)"
	
	matches = re.finditer(regex, str(response.content), re.MULTILINE | re.IGNORECASE)
	
	for match in matches:

		evl = str(match.group(1))

		if isdoi(evl):
			candidates.append((evl, "free text", 0.1))

	candidates = sorted(candidates, key = lambda x: x[0])

	condensed_candidates = []

	for key, group in groupby(candidates, lambda x: x[0]):
		score = 0
		for thing in group:
			score = score + thing[2]
    	
		condensed_candidates.append((key, "condensed", score))

	condensed_candidates = sorted(condensed_candidates, key = lambda x: x[2], reverse = True)

	if len(condensed_candidates) > 0:
		
		return str(condensed_candidates[0][0])

	else:

		return False

def get_cite_from_doi(doi, style):

	headers = {
  		'Accept': 'text/x-bibliography; style={}'.format(style),
	}

	response = requests.get('https://doi.org/{}'.format(doi), headers=headers)

	if response.ok:
		return str(response.content.decode("utf-8", "replace"))
	else:
		return False


if __name__ == "__main__":

	if len(sys.argv) < 2:

		print("\nUsage:\n     {} <paper URL or DOI number> [<citation style>]\nnote:\n     Default citation style is apa, for all citation styles see:\n     https://github.com/citation-style-language/styles\n".format(sys.argv[0]))

	else:

		urldoi = sys.argv[1]
	
		if len(sys.argv) < 3:
		 	style = "apa"
		else:
			style = sys.argv[2]
	
		if isdoi(urldoi):
			doi = urldoi
		else:
			doi = get_doi_from_url(urldoi)
			print('URL:\n     {}'.format(urldoi))
	
		if doi:
			print('DOI:\n     {}'.format(doi))
			cite = get_cite_from_doi(doi, style)
			if cite:
				print('Citation:\n     {}'.format(cite))
			else:
				print('Error:\n     {} is valid doi but is not found in database or style is invalid.'.format(doi))
		else:
			print('error: no DOI found.')
				
	
	