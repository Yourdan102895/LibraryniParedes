import sqlite3
import random
from datetime import datetime
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog, MDDialogSupportingText, MDDialogHeadlineText, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText, \
    MDListItemTertiaryText
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from library_books import books_by_category


# --- DATABASE INITIALIZATION ---
def initialize_database():
    """
    Connects to the database and creates all necessary tables if they don't exist.
    This function centralizes all table creation logic.
    """
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       student_number
                       TEXT
                       UNIQUE
                       NOT
                       NULL
                   )""")

    # Librarians table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS librarians
                   (
                       librarian_id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       password
                       TEXT
                       UNIQUE
                       NOT
                       NULL
                   )""")
    # Insert default librarian if not present
    try:
        cursor.execute("INSERT INTO librarians (name, password) VALUES (?, ?)", ('admin', 'admin'))
    except sqlite3.IntegrityError:
        pass  # Admin already exists

    # Books table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS books
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT,
                       author
                       TEXT,
                       category
                       TEXT,
                       availability
                       TEXT
                   )""")

    # Borrowed books table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS borrowed_books
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       student_name
                       TEXT,
                       student_number
                       TEXT,
                       book_title
                       TEXT,
                       book_author
                       TEXT,
                       date_borrowed
                       TEXT,
                       date_returned
                       TEXT,
                       return_status
                       TEXT
                       DEFAULT
                       'Not Returned'
                   )""")

    # Borrow requests table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS borrow_requests
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       student_number
                       TEXT,
                       student_name
                       TEXT,
                       book_title
                       TEXT,
                       book_author
                       TEXT,
                       status
                       TEXT
                       DEFAULT
                       'Pending',
                       date_requested
                       TEXT,
                       date_approved
                       TEXT
                   )""")

    # Return requests table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS return_requests
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       student_name
                       TEXT,
                       student_number
                       TEXT,
                       book_title
                       TEXT,
                       author
                       TEXT,
                       status
                       TEXT
                       DEFAULT
                       'Pending',
                       date_requested
                       TEXT,
                       date_approved
                       TEXT
                   )""")

    # Favorites table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS favorites
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       student_number
                       TEXT,
                       book_id
                       INTEGER,
                       title
                       TEXT,
                       author
                       TEXT,
                       category
                       TEXT
                   )""")

    conn.commit()
    conn.close()


# --- SCREEN CLASSES ---
# Each class corresponds to a screen defined in the .kv file.
# The `on_enter` method is called automatically when a screen is displayed.

class LoginScreen(MDScreen): pass


class RegisterScreen(MDScreen): pass


class LibrarianScreen(MDScreen): pass


class MainScreen(MDScreen): pass


class LibrarianDashboardScreen(MDScreen): pass


class HomeScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_recommended_books()


class FavoritesScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_favorites()


class SearchScreen(MDScreen):
    def on_enter(self):
        self.ids.search_results_list.clear_widgets()
        self.ids.search_field.text = ""


class CategoriesScreen(MDScreen): pass


class ViewBorrowedLibrarianScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_all_borrowed_books()


class BorrowRequestScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_borrow_requests()


class ReturnRequestScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_return_requests()


class ViewBooksScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_all_books_for_librarian()


class RegisterBooksScreen(MDScreen): pass


class ViewBorrowedScreen(MDScreen):
    def on_enter(self):
        MDApp.get_running_app().load_student_borrowed_books()


# Book Category Screens
class InformationTechnologyScreen(MDScreen):
    def on_enter(self): MDApp.get_running_app().load_books_by_category("Information Technology", self.ids.it_books_list)


class HospitalityManagementScreen(MDScreen):
    def on_enter(self): MDApp.get_running_app().load_books_by_category("Hospitality Management", self.ids.hm_books_list)


class ComputerEngineeringScreen(MDScreen):
    def on_enter(self): MDApp.get_running_app().load_books_by_category("Computer Engineering", self.ids.cpe_books_list)


class OfficeAdministrationScreen(MDScreen):
    def on_enter(self): MDApp.get_running_app().load_books_by_category("Office Administration", self.ids.oa_books_list)


class PhysicalEducationScreen(MDScreen):
    def on_enter(self): MDApp.get_running_app().load_books_by_category("PE", self.ids.pe_books_list)


# --- MAIN APP CLASS ---
class LibraryApp(MDApp):
    dialog = None
    info_dialog = None
    logged_in_student_number = StringProperty(None)

    def build(self):
        # Set theme and load the main KV file
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        # Initialize database and insert initial book data on first run
        initialize_database()
        self.insert_initial_books()
        return Builder.load_file("library.kv")

    def on_start(self):
        """Called after the build() method is finished."""
        # You can add startup logic here if needed
        pass

    # --- UTILITY FUNCTIONS ---
    def show_dialog(self, title, text):
        """A generic function to show a dialog message."""
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    on_release=lambda x: self.dialog.dismiss()
                ),
            )
        )
        self.dialog.open()

    def switch_screen(self, screen_name):
        """Switches the main screen manager to the specified screen."""
        self.root.current = screen_name

    def on_switch_tabs(self, bar: MDNavigationBar, item: MDNavigationItem, item_icon: str, item_text: str):
        """Handles tab switching on the student's main screen."""
        screen_map = {
            "Home": "home_screen",
            "Favorites": "favorites_screen",
            "Search": "search_screen",
            "Categories": "categories_screen"
        }
        target_screen = screen_map.get(item_text)
        if target_screen:
            self.root.get_screen('main_screen').ids.screen_manager.current = target_screen

    def logout(self):
        """Logs out the user and returns to the login screen."""
        self.logged_in_student_number = None
        self.root.current = 'login_screen'
        # Also reset student navigation to home
        main_screen = self.root.get_screen('main_screen')
        main_screen.ids.screen_manager.current = 'home_screen'
        main_screen.ids.navigation_bar.switch_tab("Home")

    # --- INITIAL DATA INSERTION ---
    def insert_initial_books(self):
        """Inserts books from library_books.py if they are not already in the database."""
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        for category, books in books_by_category.items():
            for book in books:
                cursor.execute("SELECT * FROM books WHERE title = ? AND author = ?", (book['title'], book['author']))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO books (title, author, category, availability) VALUES (?, ?, ?, ?)",
                                   (book['title'], book['author'], category, book['availability']))
        conn.commit()
        conn.close()

    # --- USER AND LIBRARIAN AUTHENTICATION ---
    def login_student(self, name, student_number):
        if not name.strip() or not student_number.strip():
            self.show_dialog("Login Failed", "Please enter both name and student number.")
            return
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ? AND student_number = ?", (name, student_number))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.logged_in_student_number = user[3]  # student_number is the 4th column
            self.root.current = "main_screen"
        else:
            self.show_dialog("Login Failed", "No matching student account found.")

    def register_student(self, name, email, student_number):
        if not name.strip() or not email.strip() or not student_number.strip():
            self.show_dialog("Registration Failed", "Please fill in all fields.")
            return
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? OR student_number = ?", (email, student_number))
        if cursor.fetchone():
            conn.close()
            self.show_dialog("Registration Failed", "Email or Student Number already exists.")
            return
        cursor.execute("INSERT INTO users (name, email, student_number) VALUES (?, ?, ?)",
                       (name, email, student_number))
        conn.commit()
        conn.close()
        self.show_dialog("Success", f"Student '{name}' registered successfully! You can now log in.")
        self.root.get_screen('register_screen').ids.register_name.text = ""
        self.root.get_screen('register_screen').ids.register_email.text = ""
        self.root.get_screen('register_screen').ids.register_student_number.text = ""
        self.root.current = 'login_screen'

    def login_librarian(self, name, password):
        if not name.strip() or not password.strip():
            self.show_dialog("Login Failed", "Please enter name and password.")
            return
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM librarians WHERE name = ? AND password = ?", (name, password))
        if cursor.fetchone():
            self.root.current = "librarian_dashboard_screen"
        else:
            self.show_dialog("Login Failed", "Invalid librarian credentials.")
        conn.close()

    # --- BOOK RECOMMENDATIONS AND CATEGORIES ---
    def load_recommended_books(self):
        container = self.root.get_screen("main_screen").ids.home_screen.ids.home_recommendations_list
        container.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, availability, category FROM books WHERE availability = 'Available'")
        all_books = cursor.fetchall()
        conn.close()

        if not all_books:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="No books available.")))
            return

        selected_books = random.sample(all_books, min(10, len(all_books)))

        for book_id, title, author, availability, category in selected_books:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemLeadingIcon(icon="book"))
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"by {author}"))
            item.add_widget(MDListItemTertiaryText(text=f"Category: {category}"))

            borrow_btn = MDIconButton(
                icon="book-plus-outline",
                on_release=lambda x, b_id=book_id: self.borrow_book_request(b_id)
            )
            fav_btn = MDIconButton(
                icon="heart-outline",
                on_release=lambda x, b_id=book_id, t=title, a=author, c=category: self.add_to_favorites(b_id, t, a, c)
            )

            trailing_container = MDBoxLayout(orientation='horizontal', adaptive_size=True, spacing="10dp")
            trailing_container.add_widget(borrow_btn)
            trailing_container.add_widget(fav_btn)
            item.add_widget(trailing_container)

            container.add_widget(item)

    def load_books_by_category(self, category_name, list_widget):
        list_widget.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, availability FROM books WHERE category = ?", (category_name,))
        books = cursor.fetchall()
        conn.close()

        if not books:
            list_widget.add_widget(MDListItem(MDListItemHeadlineText(text=f"No books found in {category_name}.")))
            return

        for book_id, title, author, availability in books:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemLeadingIcon(icon="book-open-page-variant-outline"))
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"by {author}"))
            item.add_widget(MDListItemTertiaryText(text=f"Status: {availability}"))

            if availability == 'Available':
                borrow_btn = MDIconButton(
                    icon="book-plus-outline",
                    on_release=lambda x, b_id=book_id: self.borrow_book_request(b_id)
                )
                fav_btn = MDIconButton(
                    icon="heart-outline",
                    on_release=lambda x, b_id=book_id, t=title, a=author, c=category_name: self.add_to_favorites(b_id,
                                                                                                                 t, a,
                                                                                                                 c)
                )

                trailing_container = MDBoxLayout(orientation='horizontal', adaptive_size=True, spacing="10dp")
                trailing_container.add_widget(borrow_btn)
                trailing_container.add_widget(fav_btn)
                item.add_widget(trailing_container)

            list_widget.add_widget(item)

    # --- FAVORITES ---
    def add_to_favorites(self, book_id, title, author, category):
        if not self.logged_in_student_number:
            self.show_dialog("Login Required", "You must be logged in to add favorites.")
            return
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM favorites WHERE student_number = ? AND book_id = ?",
                       (self.logged_in_student_number, book_id))
        if cursor.fetchone():
            self.show_dialog("Already a Favorite", "This book is already in your favorites list.")
        else:
            cursor.execute(
                "INSERT INTO favorites (student_number, book_id, title, author, category) VALUES (?, ?, ?, ?, ?)",
                (self.logged_in_student_number, book_id, title, author, category))
            conn.commit()
            self.show_dialog("Success", "Added to favorites!")
        conn.close()

    def load_favorites(self):
        container = self.root.get_screen("main_screen").ids.favorites_screen.ids.favorites_container
        container.clear_widgets()
        if not self.logged_in_student_number:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="Please log in to see your favorites.")))
            return
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT book_id, title, author, category FROM favorites WHERE student_number = ?",
                       (self.logged_in_student_number,))
        favorites = cursor.fetchall()
        conn.close()

        if not favorites:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="You have no favorite books yet.")))
            return

        for book_id, title, author, category in favorites:
            item = MDListItem(size_hint_y=None, height="80dp")
            item.add_widget(MDListItemLeadingIcon(icon="heart"))
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"by {author}"))

            remove_btn = MDIconButton(
                icon="trash-can-outline",
                on_release=lambda x, b_id=book_id: self.remove_from_favorites(b_id)
            )
            item.add_widget(remove_btn)
            container.add_widget(item)

    def remove_from_favorites(self, book_id):
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE student_number = ? AND book_id = ?",
                       (self.logged_in_student_number, book_id))
        conn.commit()
        conn.close()
        self.load_favorites()  # Refresh the list

    # --- SEARCH ---
    def search_books(self, query):
        results_list = self.root.get_screen("main_screen").ids.search_screen.ids.search_results_list
        results_list.clear_widgets()
        if not query.strip():
            return

        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        # Search in title or author
        search_query = f"%{query}%"
        cursor.execute(
            "SELECT id, title, author, category, availability FROM books WHERE title LIKE ? OR author LIKE ?",
            (search_query, search_query))
        results = cursor.fetchall()
        conn.close()

        if not results:
            results_list.add_widget(MDListItem(MDListItemHeadlineText(text="No results found.")))
            return

        for book_id, title, author, category, availability in results:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemLeadingIcon(icon="book-search-outline"))
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"by {author}"))
            item.add_widget(MDListItemTertiaryText(text=f"Status: {availability}"))

            if availability == 'Available':
                borrow_btn = MDIconButton(
                    icon="book-plus-outline",
                    on_release=lambda x, b_id=book_id: self.borrow_book_request(b_id)
                )
                item.add_widget(borrow_btn)

            results_list.add_widget(item)

    # --- BORROWING AND RETURNING (Student Side) ---
    def borrow_book_request(self, book_id):
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, author FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        cursor.execute("SELECT name FROM users WHERE student_number = ?", (self.logged_in_student_number,))
        student = cursor.fetchone()
        conn.close()

        if not book or not student:
            self.show_dialog("Error", "Book or student not found.")
            return

        title, author = book
        student_name = student[0]

        # Confirmation Dialog
        def confirm_action(instance):
            self.dialog.dismiss()
            conn_inner = sqlite3.connect("library.db")
            cursor_inner = conn_inner.cursor()
            # Check for existing pending request
            cursor_inner.execute("""
                                 SELECT *
                                 FROM borrow_requests
                                 WHERE student_number = ?
                                   AND book_title = ?
                                   AND status = 'Pending'
                                 """, (self.logged_in_student_number, title))
            if cursor_inner.fetchone():
                self.show_dialog("Request Exists", "You already have a pending borrow request for this book.")
            else:
                date_requested = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor_inner.execute("""
                                     INSERT INTO borrow_requests (student_number, student_name, book_title, book_author, date_requested)
                                     VALUES (?, ?, ?, ?, ?)
                                     """, (self.logged_in_student_number, student_name, title, author, date_requested))
                conn_inner.commit()
                self.show_dialog("Success", "Your borrow request has been sent to the librarian.")
            conn_inner.close()

        self.show_dialog("Confirm Borrow", f"Request to borrow '{title}'?")
        # Replace the default button action
        self.dialog.children[0].children[0].on_release = lambda: confirm_action(None)
        self.dialog.children[0].add_widget(
            MDButton(MDButtonText(text="Cancel"), on_release=lambda x: self.dialog.dismiss()))

    def return_book_request(self, title, author):
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE student_number = ?", (self.logged_in_student_number,))
        student = cursor.fetchone()

        # Check for existing pending return request
        cursor.execute("""
                       SELECT *
                       FROM return_requests
                       WHERE student_number = ?
                         AND book_title = ?
                         AND status = 'Pending'
                       """, (self.logged_in_student_number, title))

        if cursor.fetchone():
            self.show_dialog("Request Exists", "You already have a pending return request for this book.")
            conn.close()
            return

        student_name = student[0]
        date_requested = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
                       INSERT INTO return_requests (student_number, student_name, book_title, author, date_requested,
                                                    status)
                       VALUES (?, ?, ?, ?, ?, 'Pending')
                       """, (self.logged_in_student_number, student_name, title, author, date_requested))
        conn.commit()
        conn.close()
        self.show_dialog("Success", "Your return request has been sent to the librarian.")
        self.load_student_borrowed_books()  # Refresh list

    def load_student_borrowed_books(self):
        container = self.root.get_screen('view_borrowed_screen').ids.student_borrowed_books_list
        container.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT book_title, book_author, date_borrowed, date_returned, return_status FROM borrowed_books WHERE student_number = ?",
            (self.logged_in_student_number,))
        borrowed_books = cursor.fetchall()
        conn.close()

        if not borrowed_books:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="You have not borrowed any books.")))
            return

        for title, author, date_borrowed, date_returned, status in borrowed_books:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"Borrowed: {date_borrowed.split(' ')[0]}"))
            item.add_widget(MDListItemTertiaryText(text=f"Status: {status}"))

            if status == "Not Returned":
                return_btn = MDIconButton(
                    icon="book-arrow-left-outline",
                    on_release=lambda x, t=title, a=author: self.return_book_request(t, a)
                )
                item.add_widget(return_btn)

            container.add_widget(item)

    # --- LIBRARIAN FUNCTIONS ---
    def register_book(self, title, author, category, availability):
        if not all([title.strip(), author.strip(), category.strip(), availability.strip()]):
            self.show_dialog("Error", "Please fill all fields.")
            return
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, category, availability) VALUES (?, ?, ?, ?)",
                       (title, author, category, availability))
        conn.commit()
        conn.close()
        self.show_dialog("Success", f"Book '{title}' registered successfully!")
        # Clear fields
        reg_screen = self.root.get_screen('register_books_screen')
        reg_screen.ids.register_book_title.text = ""
        reg_screen.ids.register_book_author.text = ""
        reg_screen.ids.register_book_category.text = ""
        reg_screen.ids.register_book_availability.text = ""

    def load_all_books_for_librarian(self):
        container = self.root.get_screen('view_books_screen').ids.all_books_list
        container.clear_widgets()
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, category, availability FROM books")
        books = cursor.fetchall()
        conn.close()

        for book_id, title, author, category, availability in books:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemHeadlineText(text=f"{title} (ID: {book_id})"))
            item.add_widget(MDListItemSupportingText(text=f"by {author}"))
            item.add_widget(MDListItemTertiaryText(text=f"Category: {category} | Status: {availability}"))
            delete_btn = MDIconButton(
                icon="trash-can-outline",
                on_release=lambda x, b_id=book_id: self.delete_book(b_id)
            )
            item.add_widget(delete_btn)
            container.add_widget(item)

    def delete_book(self, book_id):
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        self.load_all_books_for_librarian()  # Refresh the list

    def load_borrow_requests(self):
        container = self.root.get_screen("borrow_request_screen").ids.borrow_requests_container
        container.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, student_name, student_number, book_title, book_author, status, date_requested FROM borrow_requests WHERE status = 'Pending'")
        requests = cursor.fetchall()
        conn.close()

        if not requests:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="No pending borrow requests.")))
            return

        for req_id, name, number, title, author, status, date in requests:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemHeadlineText(text=f"{name} ({number})"))
            item.add_widget(MDListItemSupportingText(text=f"wants to borrow '{title}'"))
            item.add_widget(MDListItemTertiaryText(text=f"Requested on: {date.split(' ')[0]}"))

            approve_btn = MDIconButton(icon="check",
                                       on_release=lambda x, r_id=req_id: self.update_borrow_status(r_id, "Approved"))
            reject_btn = MDIconButton(icon="close",
                                      on_release=lambda x, r_id=req_id: self.update_borrow_status(r_id, "Rejected"))

            trailing_container = MDBoxLayout(orientation='horizontal', adaptive_size=True, spacing="10dp")
            trailing_container.add_widget(approve_btn)
            trailing_container.add_widget(reject_btn)
            item.add_widget(trailing_container)

            container.add_widget(item)

    def update_borrow_status(self, request_id, new_status):
        date_approved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT student_name, student_number, book_title, book_author FROM borrow_requests WHERE id=?",
                       (request_id,))
        request = cursor.fetchone()

        if request and new_status == "Approved":
            s_name, s_num, b_title, b_author = request
            cursor.execute(
                "INSERT INTO borrowed_books (student_name, student_number, book_title, book_author, date_borrowed) VALUES (?, ?, ?, ?, ?)",
                (s_name, s_num, b_title, b_author, date_approved))
            cursor.execute("UPDATE books SET availability = 'Not Available' WHERE title = ? AND author = ?",
                           (b_title, b_author))

        cursor.execute("UPDATE borrow_requests SET status = ?, date_approved = ? WHERE id = ?",
                       (new_status, date_approved, request_id))
        conn.commit()
        conn.close()
        self.load_borrow_requests()  # Refresh list

    def load_return_requests(self):
        container = self.root.get_screen("return_request_screen").ids.return_requests_container
        container.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, student_name, student_number, book_title, author, date_requested FROM return_requests WHERE status = 'Pending'")
        requests = cursor.fetchall()
        conn.close()

        if not requests:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="No pending return requests.")))
            return

        for req_id, name, number, title, author, date in requests:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemHeadlineText(text=f"{name} ({number})"))
            item.add_widget(MDListItemSupportingText(text=f"wants to return '{title}'"))
            item.add_widget(MDListItemTertiaryText(text=f"Requested on: {date.split(' ')[0]}"))

            approve_btn = MDIconButton(icon="check",
                                       on_release=lambda x, r_id=req_id: self.update_return_status(r_id, "Approved"))
            reject_btn = MDIconButton(icon="close",
                                      on_release=lambda x, r_id=req_id: self.update_return_status(r_id, "Rejected"))

            trailing_container = MDBoxLayout(orientation='horizontal', adaptive_size=True, spacing="10dp")
            trailing_container.add_widget(approve_btn)
            trailing_container.add_widget(reject_btn)
            item.add_widget(trailing_container)

            container.add_widget(item)

    def update_return_status(self, request_id, new_status):
        date_approved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("SELECT book_title, author, student_number FROM return_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()

        if request and new_status == "Approved":
            title, author, number = request
            cursor.execute("UPDATE books SET availability = 'Available' WHERE title = ? AND author = ?",
                           (title, author))
            cursor.execute(
                "UPDATE borrowed_books SET date_returned = ?, return_status = 'Returned' WHERE student_number = ? AND book_title = ?",
                (date_approved, number, title))

        cursor.execute("UPDATE return_requests SET status = ?, date_approved = ? WHERE id = ?",
                       (new_status, date_approved, request_id))
        conn.commit()
        conn.close()
        self.load_return_requests()

    def load_all_borrowed_books(self):
        container = self.root.get_screen("view_borrowed_librarian_screen").ids.borrowed_books_list
        container.clear_widgets()
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_name, student_number, book_title, date_borrowed, return_status FROM borrowed_books")
        books = cursor.fetchall()
        conn.close()

        if not books:
            container.add_widget(MDListItem(MDListItemHeadlineText(text="No books have been borrowed.")))
            return

        for name, number, title, date_borrowed, status in books:
            item = MDListItem(size_hint_y=None, height="100dp")
            item.add_widget(MDListItemHeadlineText(text=title))
            item.add_widget(MDListItemSupportingText(text=f"Borrowed by: {name} ({number})"))
            item.add_widget(MDListItemTertiaryText(text=f"Date: {date_borrowed.split(' ')[0]} | Status: {status}"))
            container.add_widget(item)


if __name__ == "__main__":
    LibraryApp().run()
