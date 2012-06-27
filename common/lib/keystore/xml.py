from fs.osfs import OSFS
from importlib import import_module
from lxml import etree
from path import path
from xmodule.x_module import XModuleDescriptor, XMLParsingSystem

from . import ModuleStore, Location
from .exceptions import ItemNotFoundError


class XMLModuleStore(ModuleStore):
    """
    An XML backed ModuleStore
    """
    def __init__(self, org, course, data_dir, default_class=None):
        self.data_dir = path(data_dir)
        self.modules = {}

        module_path, _, class_name = default_class.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        self.default_class = class_

        with open(data_dir / "course.xml") as course_file:
            class ImportSystem(XMLParsingSystem):
                def __init__(self, keystore):
                    self.unnamed_modules = 0

                    def process_xml(xml):
                        try:
                            xml_data = etree.fromstring(xml)
                        except:
                            print xml
                            raise
                        if xml_data.get('name'):
                            xml_data.set('slug', Location.clean(xml_data.get('name')))
                        else:
                            self.unnamed_modules += 1
                            xml_data.set('slug', '{tag}_{count}'.format(tag=xml_data.tag, count=self.unnamed_modules))

                        module = XModuleDescriptor.load_from_xml(etree.tostring(xml_data), self, org, course, keystore.default_class)
                        keystore.modules[module.url] = module
                        return module

                    XMLParsingSystem.__init__(self, keystore.get_item, OSFS(data_dir), process_xml)

            ImportSystem(self).process_xml(course_file.read())

    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the most item with the most
        recent revision

        If any segment of the location is None except revision, raises
            keystore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """
        location = Location(location)
        try:
            return self.modules[location.url()]
        except KeyError:
            raise ItemNotFoundError(location)

    def create_item(self, location):
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError("XMLModuleStores are read-only")
