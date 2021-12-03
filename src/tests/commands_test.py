import unittest
from commands.commands import Add, Show, Edit, Search, Unknown
from unittest.mock import Mock
from entities.bookmark import Bookmark

class TestCommands(unittest.TestCase):
    def setUp(self):
        self.io = Mock()
        self.service = Mock()
        self.add = Add(self.io, self.service)
        self.bookmark = Bookmark(1, "Test", "test.com")

    def test_print_correct_message_when_there_are_not_any_bookmarks_to_show(self):
        self.service.get_all.return_value = None
        show = Show(self.io, self.service)

        show.execute()

        self.io.write.assert_called_with("No bookmarks")
    
    def test_print_titles_of_all_bookmarks(self):
        self.service.get_all.return_value = [self.bookmark]
        self.show = Show(self.io, self.service)
        
        self.show.execute()

        self.io.write.assert_called_with("1 Test")
    
    def test_print_marched_titles(self):
        self.io.read.return_value = "Test"
        self.service.get_by_title.return_value = [self.bookmark]
        search = Search(self.io, self.service)

        search.execute()

        self.io.write.assert_called_with("1 Test")
    
    def test_print_accepted_commands_when_unknown_command_was_given(self):
        unknown = Unknown(self.io)

        unknown.execute()

        self.io.write.assert_called_with("""
            Acceptable commands:
            'q' - quit,
            'h' - help,
            'add' - add a new bookmark,
            'show' - show given amount of bookmarks,
            'search' - search bookmarks by a term,
            'edit' - edit a bookmark
        """)
