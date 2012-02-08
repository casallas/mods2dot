#!/usr/bin/env python
# encoding: utf-8
#
# Convert an XML MODS file into a GraphViz "dot" or "gv" file
# No links are made (yet) between the nodes

import sys
import codecs 			#for Unicode file writing
from lxml import etree

class RefAuthor:
	def __init__(self, given_name, family_name):
		self.given_name = given_name
		self.family_name = family_name

class Host:
	def __init__(self, title, genre):
		self.title = title
		self.genre = genre#Conference, journal

class AcademicReference:
	def __init__(self, id, title, authors, year, host):
		self.id = id
		self.title = title
		self.authors = authors
		self.year = year
		self.host = host
	
	def authors_str(self):
		if not self.authors:
			return "anonymous"
		ans = ""
		for i in range(len(self.authors)):
			if i is 0:
				pass
			elif i is len(self.authors)-1:
				ans += " & "
			else:
				ans += ", "
			ans += self.authors[i].family_name
		return ans
		
	def to_dot_node(self):
		ans = self.id 
		ans += " [style=filled, fillcolor=white,"
		ans += " label=\"" + self.authors_str() 
		ans += " | " + str(self.year)
		if self.host:
			ans += " | " + self.host.title
		ans += "\"];"
		return ans

class DotDigraph:
	def __init__(self):
		self.header = "digraph\n{"
		self.header += "\n"
		self.header += "\tnode [shape=record, fontsize=12];\n"
		self.header += "\tgraph [splines=true];\n"
		self.header += "\trankdir=LR;\n"
		self.header += "\n"
		self.references = []
	
	def to_str(self):
		ans = self.header
		for i in range(len(self.references)):
			ans += "\t" + self.references[i].to_dot_node() + "\n"
		ans += "}"
		return ans

xmlns = "{http://www.loc.gov/mods/v3}"

class AcademicReferenceModsParser:
	def __init__(self):
		self.id = ""
		self.title = ""
		self.authors = []
		self.year = "1900"
		self.host = None
	
	def parse_reference(self,element):
		if element.tag.startswith(xmlns+"mods"):
			self.id = element.get("ID")
			for subelement in element:
				if subelement.tag.startswith(xmlns+"titleInfo"):
					self.parse_title(subelement)
				elif subelement.tag.startswith(xmlns+"name"):
					self.parse_name(subelement)
				elif subelement.tag.startswith(xmlns+"originInfo"):
					self.parse_origin(subelement)
				elif subelement.tag.startswith(xmlns+"relatedItem"):
					self.parse_host(subelement)
			return True
		else:
			return False
	
	def parse_title(self,element):
		self.title = self._parse_titleInfo(element)["title"]
		if self.title is None:
			self.title = ""
	
	def parse_name(self,element):
		given = ""
		family = ""
		for subelement in element:
			if subelement.get("type") == "given":
				given += subelement.text
			elif subelement.get("type") == "family":
				family += subelement.text
		rAuth = RefAuthor(given,family)
		self.authors.append(rAuth)
	
	def parse_origin(self,element):
		date = self._parse_originInfo(element)["dateIssued"]
		self.year = "" if date is None else date.partition("-")[0]
	
	def parse_host(self,element):
		host_title = ""
		host_genre = ""
		if element.get("type") == "host":
			for subelement in element:
				if subelement.tag.startswith(xmlns+"titleInfo"):
					host_title = self._parse_titleInfo(element[0])["title"]
				elif subelement.tag.startswith(xmlns+"genre"):
					host_genre = subelement.text
		self.host = Host(host_title,host_genre)
	
	def get_AcademicReference(self):
		return AcademicReference(self.id, self.title,\
		self.authors, self.year, self.host)
	
	def _parse_titleInfo(self,element):
		return { "title" : element.findtext(xmlns+"title"),\
		"subTitle" : element.findtext(xmlns+"subTitle") }#might be None
		
	def _parse_originInfo(self,element):
		return { "dateIssued" : element.findtext(xmlns+"dateIssued"),\
		"publisher" : element.findtext(xmlns+"publisher") }#still missing some data

def parse_mods(tree):
	references = []
	for element in tree.iter(xmlns+"mods"):
		arp = AcademicReferenceModsParser()
		arp.parse_reference(element)
		references.append(arp.get_AcademicReference())
	return references


if __name__ == "__main__":
	if sys.argv[1] == '--help' or sys.argv[1] == '-h':
		print 'Usage: '+sys.argv[0]+' input [output]'
	else:
		tree = etree.parse(sys.argv[1])
		dotDG = DotDigraph()
		dotDG.references = parse_mods(tree)
		output = dotDG.to_str()
		if len(sys.argv)==3:
			outFile = codecs.open(sys.argv[2],encoding='utf-8', mode='w')
			outFile.write(output)
			outFile.close()
		else:
			print output
