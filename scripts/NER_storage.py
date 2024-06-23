from lxml import etree
import os

def extract_entities(directory, output_persons, output_places):
    # Define the namespaces used in your XML files
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # Open files to write the extracted entities
    with open(output_persons, 'w', encoding='utf-8') as persons_file, \
         open(output_places, 'w', encoding='utf-8') as places_file:
        # Iterate through all XML files in the given directory
        for filename in os.listdir(directory):
            if filename.endswith('.xml'):
                # Construct the full file path
                file_path = os.path.join(directory, filename)
                # Parse the XML file
                tree = etree.parse(file_path)
                
                # Extract and write person names, ignoring those with ref="auto-name" or ref="auto"
                for person in tree.xpath('//tei:persName[not(@ref="auto-name") and not(@ref="auto") and not(@type="auto_name")]', namespaces=namespaces):
                    person_name = person.text.strip() if person.text else ''  # Remove leading and trailing white spaces
                    if person.getparent().tag.endswith('}persName'):  # Check if parent is persName within the TEI namespace
                        # Check children of persName
                        pers_children = person.getchildren()
                        for child in pers_children:
                            if child.tag.endswith('}i'):  # Check if child is 'i' within the TEI namespace
                                person_name += ' ' + (child.text.strip() if child.text else '')
                    person_id = person.get('ref')  # Get the id attribute
                    if person_name:  # Only write non-empty names
                        persons_file.write(f'{person_name}, {person_id}\n' if person_id else f'{person_name}\n')

                # Extract and write place names, ignoring those with ref="auto-name" or ref="auto"
                for place in tree.xpath('//tei:placeName[not(@ref="auto-name") and not(@ref="auto") and not(@type="auto_name")]', namespaces=namespaces):
                    place_name = place.text.strip() if place.text else ''  # Remove leading and trailing white spaces
                    place_id = place.get('ref')  # Get the id attribute
                    if place_name:  # Only write non-empty names
                        places_file.write(f'{place_name}, {place_id}\n' if place_id else f'{place_name}\n')


# Specify the input directory and output files
input_directory = '/Users/isabellecretton/Desktop/UGBERT/SEMESTER_4/CREATION-ANNOTATION/project/calir-bullingerproject/letters_ohne_GS'
output_persons = 'extracted_persons.txt'
output_places = 'extracted_places.txt'

# Run the function
extract_entities(input_directory, output_persons, output_places)

