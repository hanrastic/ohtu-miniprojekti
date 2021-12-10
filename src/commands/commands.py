import os
import sys
import json
from datetime import datetime
from ui.app_state import app_state

class InvalidInputException(Exception):
    pass

class CommandStoppedException(Exception):
    pass

class Command:
    def __init__(self, io, service=None):
        self.io = io
        self.service = service
    
    def execute(self, argv):
        self._run_command(argv)
    
    def _read_new_arg(self, prompt, title='') -> str:
        if title != '':
            self.io.write(title)
        arg = self.io.read(prompt, self.io.get_cursor())
        if arg.strip() == 'b':
            raise CommandStoppedException()
        return arg

    def _get_int(self, arg):
        result = None
        try:
            result = int(arg)
        except:
            pass
        return result
    
    def invalid(self, conditions=None):
        if conditions != None:
            conditions = conditions.help()
        self.io.write(f"Invalid command!\n{conditions}")
    
    def _run_command(self, argv):
        self.io.clear()
        pass

    
class Help(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        Unknown._run_command(self, argv)
        self.io.write("""
            To delete a bookmark, first choose 'select', type the ID of the bookmark and then 'delete'
        """)

class Add(Command):    
    def _run_command(self, argv):
        super()._run_command(argv)
        self.url = self._read_new_arg("Url: ", "New bookmark")

        url_title = self.service.get_title_by_url(self.url)
        if url_title is None:
            raise InvalidInputException("Invalid url")
        
        title = self._set_title(url_title)
        bookmark = self.service.create(self.url, title)
        self.io.write(f'\nBookmark "{bookmark.short_str()}" created!')
    
    def _set_title(self, url_title):
        user_input = ''
        while user_input not in ['y', 'n']:
            self.io.write('')
            user_input = self.io.read_chr(f'Do you want to keep the title "{url_title}"? [y/n]')
        if user_input == 'n':
            return self._create_new_title()
        return url_title
    
    def _create_new_title(self):
        self.io.clear()
        return self._read_new_arg("Title: ", f'New bookmark\nUrl: {self.url}')

class Show(Command):

    def help(self):
        return """Search usage:
        \n  get all: search | get all, limit selection: search <int> | get range: search <int> <int>
        """

    def _run_command(self, argv):
        super()._run_command(argv)
        if len(argv) == 0:
            self._show_all()
        elif len(argv) == 1:
            count = self._get_int(argv[0])
            if count != None:
                self._show_range(0, count)
            elif argv[0] == 'help':
                self._help()
            else:
                self.invalid(self)
        elif len(argv) >= 2:
            start = self._get_int(argv[0])
            count = self._get_int(argv[1])
            if start != None and count != None:
                self._show_range(start, count)
            else:
                self.invalid(self)
    
    def _show_all(self):
        bookmarks = self.service.get_all()
        if not bookmarks:
            self.io.write("No bookmarks")
        else:
            self.io.print_bookmarks(bookmarks)

    def _show_range(self, start, count):
        bookmarks = self.service.get_all(start, count)
        if not bookmarks:
            self.io.write("No bookmarks")
            return
        self.io.print_bookmarks(bookmarks)

class Edit(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        raise InvalidInputException("Edit-command is not yet implemented")

class Delete(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        if app_state.selected is None and not argv:
            raise InvalidInputException("Please select a bookmark to delete it")
        deletations = argv if app_state.selected is None else [app_state.selected.id]
        for id in deletations:
            if self.service.delete(id):
                self.io.write(f"Bookmark {id} deleted successfully")
            else:
                raise InvalidInputException(f"Bookmark {id} didn't exist!")
        app_state.selected = None
            

class Select(Command):

    def help(self):
        return """
            To delete a bookmark: type in ID of the bookmark, press enter and then type 'delete'
            To edit a bookmark: type in ID of the bookmark, press enter and then type 'edit'
            To go back: type in 'b'
        """

    def _run_command(self, argv):
        id = None
        if len(argv) > 0:
            id = self._get_int(argv[0])

        if id is None:
            id = self._get_int(self._read_new_arg("enter bookmark id: ", "Bookmark selector"))    
            if id is None:
                self.invalid(self)
                return

        self.io.clear()
        bookmark = self.service.get_one(id)
        if bookmark is None:
            raise InvalidInputException("Bookmark selector\nInvalid id")
        app_state.selected = bookmark
        self.io.write("Selected " + bookmark.short_str() + "\n")
        user_input = ''
        while user_input not in ['e','d','b']:
            self.io.write('',-2)
            user_input = self.io.read_chr('\nAvailable commands: [e]dit, [d]elete, [b]ack')
        if user_input == 'e':
            Edit(self.io, self.service)._run_command([id])
        elif user_input == 'd':
            Delete(self.io, self.service)._run_command([id])
        app_state.selected = None

class Search(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        if argv and argv[0] == 'url':
            if len(argv) == 1:
                term = self._read_new_arg("Url:", "Search")
            else:
                term = argv[1]
            search_method = self.search_by_url
        else:
            if argv:
                term = argv[0]
            else:
                term = self._read_new_arg("Term: ", "Search")
            search_method = self.search_by_title

        search_method(term)

    def search_by_url(self, url):
        bookmarks = self.service.get_by_url(url)
        self.parse_results(bookmarks, "Could not find any bookmarks with that url")

    def search_by_title(self, title):
        bookmarks = self.service.get_by_title(title)
        self.parse_results(bookmarks, "Could not find any bookmarks with that title")

    def parse_results(self, bookmarks, msg):
        if not bookmarks:
            raise InvalidInputException(msg)
        self.io.print_bookmarks(bookmarks, "Search results")
        self.io.write(f"Found {len(bookmarks)} results", 1)

class Quit(Command):
    def _run_command(self, argv):
        self.io.exit("  Have a nice day!")
        sys.exit(0)

class Export(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        bookmarks = self.service.get_all()
        if bookmarks:
            data = self.convert_to_json(bookmarks)
            self.write_to_file(data, argv)

    def convert_to_json(self, bookmarks):
        data = {}
        data["bookmarks"] = []
        for bookmark in bookmarks:
            data["bookmarks"].append({
                "title": bookmark.title,
                "url": bookmark.url
            })
        return data
    
    def write_to_file(self, data, argv):
        if len(argv) == 1:
            path = self.check_path(str(argv[0]))
            with open(path, "w") as outfile:
                json.dump(data, outfile, sort_keys=True, indent=4)
                self.io.write("Exported successfully!")
        else:
            with open("export/" + str(datetime.now()) + ".json", "w") as outfile:
                json.dump(data, outfile, sort_keys=True, indent=4)
                self.io.write("Exported successfully!")
    
    def check_path(self, path):
        if path.find("export/") != 0:
            path = "export/" + path
        if os.path.splitext(path)[1] != ".json":
            path += ".json"
        return path

class ImportJson(Command):

    def _run_command(self, argv):
        super()._run_command(argv)
        if len(argv) == 0:
            raise InvalidInputException("Import argument missing")
        try:
            with open(argv[0], "r") as file:
                data = json.load(file)
        except:
            raise InvalidInputException("File not found")

        #if not self.validate_json(data):
        #    raise InvalidInputException("Invalid file format")

        self.add_bookmarks_to_repository(data)
        self.io.write("Bookmarks imported successfully!")

    def add_bookmarks_to_repository(self, data):
        added = []
        
        for entry_bookmark in data["db"]:
            bookmark = self.service.create(entry_bookmark["url"], entry_bookmark["title"])
            if bookmark is not None:
                added.append(bookmark)
                self.io.write(bookmark.short_str())
            else:
                self.io.write("Invalid bookmark")
            
        return added
    
    # def validate_json(self, data):
        # valid_schema = {
        #     "title": "string",
        #     "url": "string"
        # }
        # try:
        #     validate(data, valid_schema)
        # except ValidationError as error:
        #     return False
        # return True

    
    
class Unknown(Command):
    def _run_command(self, argv):
        super()._run_command(argv)
        self.io.write('command unrecognized.')
        self.io.write("""
            Acceptable commands:
            'q' - quit,
            'h' - help,
            'b' - back,
            'add' - add a new bookmark,
            'show' - show given amount of bookmarks,
            'search' - search bookmarks by a term,
            'select' - select a bookmark
            'edit' - edit a selected bookmark
            'delete' - delete a selected bookmark
        """)