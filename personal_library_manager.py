import streamlit as st
import json
import os
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any, Union
import re

class Book:
    """Class representing a book in the personal library."""
    
    def __init__(self, 
                 title: str, 
                 author: str, 
                 isbn: str = "", 
                 genre: str = "", 
                 year: int = None, 
                 publisher: str = "", 
                 pages: int = None, 
                 description: str = "",
                 location: str = "Shelf",
                 status: str = "Available",
                 rating: int = None,
                 date_added: str = None,
                 tags: List[str] = None):
        """Initialize a new Book object."""
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.year = year
        self.publisher = publisher
        self.pages = pages
        self.description = description
        self.location = location
        self.status = status  # Available, Borrowed, Lost, etc.
        self.rating = rating  # 1-5 stars
        
        # Set date_added to current date if not provided
        if date_added is None:
            self.date_added = datetime.datetime.now().strftime("%Y-%m-%d")
        else:
            self.date_added = date_added
            
        # Initialize borrowing info
        self.borrowed_by = ""
        self.borrowed_date = ""
        self.due_date = ""
        
        # Initialize tags
        self.tags = tags if tags is not None else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Book object to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "genre": self.genre,
            "year": self.year,
            "publisher": self.publisher,
            "pages": self.pages,
            "description": self.description,
            "location": self.location,
            "status": self.status,
            "rating": self.rating,
            "date_added": self.date_added,
            "borrowed_by": self.borrowed_by,
            "borrowed_date": self.borrowed_date,
            "due_date": self.due_date,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        """Create a Book object from a dictionary."""
        book = cls(
            title=data["title"],
            author=data["author"],
            isbn=data.get("isbn", ""),
            genre=data.get("genre", ""),
            year=data.get("year"),
            publisher=data.get("publisher", ""),
            pages=data.get("pages"),
            description=data.get("description", ""),
            location=data.get("location", "Shelf"),
            status=data.get("status", "Available"),
            rating=data.get("rating"),
            date_added=data.get("date_added"),
            tags=data.get("tags", [])
        )
        
        # Set borrowing info
        book.borrowed_by = data.get("borrowed_by", "")
        book.borrowed_date = data.get("borrowed_date", "")
        book.due_date = data.get("due_date", "")
        
        return book
    
    def lend(self, borrower: str, days: int = 14) -> None:
        """Mark the book as borrowed."""
        if self.status != "Available":
            raise ValueError(f"Book is not available. Current status: {self.status}")
        
        self.status = "Borrowed"
        self.borrowed_by = borrower
        today = datetime.datetime.now()
        self.borrowed_date = today.strftime("%Y-%m-%d")
        due_date = today + datetime.timedelta(days=days)
        self.due_date = due_date.strftime("%Y-%m-%d")
    
    def return_book(self) -> None:
        """Mark the book as returned."""
        if self.status != "Borrowed":
            raise ValueError(f"Book is not borrowed. Current status: {self.status}")
        
        self.status = "Available"
        self.borrowed_by = ""
        self.borrowed_date = ""
        self.due_date = ""
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the book."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the book."""
        if tag in self.tags:
            self.tags.remove(tag)


class Library:
    """Class representing a personal library collection."""
    
    def __init__(self, name: str = "My Personal Library"):
        """Initialize a new Library object."""
        self.name = name
        self.books: List[Book] = []
        self.file_path = "library_data.json"
    
    def add_book(self, book: Book) -> None:
        """Add a book to the library."""
        # Check if book with same title and author already exists
        for existing_book in self.books:
            if (existing_book.title.lower() == book.title.lower() and 
                existing_book.author.lower() == book.author.lower()):
                raise ValueError(f"Book '{book.title}' by {book.author} already exists in the library.")
        
        self.books.append(book)
    
    def remove_book(self, book_id: int) -> Book:
        """Remove a book from the library by its ID."""
        if 0 <= book_id < len(self.books):
            removed_book = self.books.pop(book_id)
            return removed_book
        else:
            raise ValueError(f"Invalid book ID: {book_id}")
    
    def get_book(self, book_id: int) -> Book:
        """Get a book by its ID."""
        if 0 <= book_id < len(self.books):
            return self.books[book_id]
        else:
            raise ValueError(f"Invalid book ID: {book_id}")
    
    def update_book(self, book_id: int, **kwargs) -> None:
        """Update a book's information."""
        if 0 <= book_id < len(self.books):
            book = self.books[book_id]
            
            for key, value in kwargs.items():
                if hasattr(book, key):
                    setattr(book, key, value)
        else:
            raise ValueError(f"Invalid book ID: {book_id}")
    
    def search_books(self, query: str, fields: List[str] = None) -> List[int]:
        """
        Search for books matching the query in specified fields.
        Returns a list of book IDs that match the search criteria.
        """
        if fields is None:
            fields = ["title", "author", "isbn", "genre", "publisher", "description", "tags"]
        
        results = []
        query = query.lower()
        
        for i, book in enumerate(self.books):
            for field in fields:
                if field == "tags" and hasattr(book, "tags"):
                    # Search in tags list
                    if any(query in tag.lower() for tag in book.tags):
                        results.append(i)
                        break
                elif hasattr(book, field):
                    value = getattr(book, field)
                    if value is not None and query in str(value).lower():
                        results.append(i)
                        break
        
        return results
    
    def filter_books(self, **kwargs) -> List[int]:
        """
        Filter books based on exact matches for specified attributes.
        Returns a list of book IDs that match the filter criteria.
        """
        results = []
        
        for i, book in enumerate(self.books):
            match = True
            
            for key, value in kwargs.items():
                if key == "year_from" and hasattr(book, "year") and book.year is not None:
                    if book.year < value:
                        match = False
                        break
                elif key == "year_to" and hasattr(book, "year") and book.year is not None:
                    if book.year > value:
                        match = False
                        break
                elif key == "rating_from" and hasattr(book, "rating") and book.rating is not None:
                    if book.rating < value:
                        match = False
                        break
                elif key == "rating_to" and hasattr(book, "rating") and book.rating is not None:
                    if book.rating > value:
                        match = False
                        break
                elif hasattr(book, key):
                    book_value = getattr(book, key)
                    if book_value != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                results.append(i)
        
        return results
    
    def save_to_file(self, file_path: str = None) -> None:
        """Save the library to a JSON file."""
        if file_path is not None:
            self.file_path = file_path
        
        data = {
            "name": self.name,
            "books": [book.to_dict() for book in self.books]
        }
        
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_file(self, file_path: str = None) -> None:
        """Load the library from a JSON file."""
        if file_path is not None:
            self.file_path = file_path
        
        if not os.path.exists(self.file_path):
            return
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            self.name = data.get("name", "My Personal Library")
            self.books = [Book.from_dict(book_data) for book_data in data.get("books", [])]
        except json.JSONDecodeError:
            st.error(f"Error: {self.file_path} is not a valid JSON file.")
        except Exception as e:
            st.error(f"Error loading library: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the library."""
        if not self.books:
            return {
                "total_books": 0,
                "available_books": 0,
                "borrowed_books": 0,
                "genres": {},
                "authors": {},
                "years": {},
                "ratings": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, "unrated": 0},
                "tags": {},
                "avg_rating": 0,
                "oldest_book": None,
                "newest_book": None
            }
        
        stats = {
            "total_books": len(self.books),
            "available_books": sum(1 for book in self.books if book.status == "Available"),
            "borrowed_books": sum(1 for book in self.books if book.status == "Borrowed"),
            "genres": {},
            "authors": {},
            "years": {},
            "ratings": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, "unrated": 0},
            "tags": {},
            "avg_rating": 0,
            "oldest_book": None,
            "newest_book": None
        }
        
        total_rating = 0
        rated_books = 0
        
        for book in self.books:
            # Count genres
            if book.genre:
                stats["genres"][book.genre] = stats["genres"].get(book.genre, 0) + 1
            
            # Count authors
            stats["authors"][book.author] = stats["authors"].get(book.author, 0) + 1
            
            # Count years
            if book.year:
                stats["years"][book.year] = stats["years"].get(book.year, 0) + 1
                
                # Track oldest and newest books
                if stats["oldest_book"] is None or book.year < stats["oldest_book"][1]:
                    stats["oldest_book"] = (book.title, book.year)
                
                if stats["newest_book"] is None or book.year > stats["newest_book"][1]:
                    stats["newest_book"] = (book.title, book.year)
            
            # Count ratings
            if book.rating:
                stats["ratings"][book.rating] = stats["ratings"].get(book.rating, 0) + 1
                total_rating += book.rating
                rated_books += 1
            else:
                stats["ratings"]["unrated"] += 1
            
            # Count tags
            for tag in book.tags:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
        
        # Calculate average rating
        if rated_books > 0:
            stats["avg_rating"] = round(total_rating / rated_books, 2)
        
        # Sort dictionaries by value (descending)
        stats["genres"] = dict(sorted(stats["genres"].items(), key=lambda x: x[1], reverse=True))
        stats["authors"] = dict(sorted(stats["authors"].items(), key=lambda x: x[1], reverse=True))
        stats["years"] = dict(sorted(stats["years"].items(), key=lambda x: x[1], reverse=True))
        stats["tags"] = dict(sorted(stats["tags"].items(), key=lambda x: x[1], reverse=True))
        
        return stats


# Initialize session state variables if they don't exist
def init_session_state():
    if 'library' not in st.session_state:
        st.session_state.library = Library()
        st.session_state.library.load_from_file()
    
    if 'current_book_id' not in st.session_state:
        st.session_state.current_book_id = None
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    if 'filter_results' not in st.session_state:
        st.session_state.filter_results = []
    
    if 'show_book_details' not in st.session_state:
        st.session_state.show_book_details = False


# Function to create a book dataframe for display
def create_book_dataframe(book_ids=None):
    library = st.session_state.library
    
    if not library.books:
        return pd.DataFrame()
    
    if book_ids is None:
        book_ids = range(len(library.books))
    
    data = []
    for i in book_ids:
        if i < len(library.books):
            book = library.books[i]
            data.append({
                "ID": i,
                "Title": book.title,
                "Author": book.author,
                "Year": book.year if book.year else "",
                "Genre": book.genre if book.genre else "",
                "Status": book.status,
                "Rating": "★" * book.rating if book.rating else "",
                "Tags": ", ".join(book.tags) if book.tags else ""
            })
    
    return pd.DataFrame(data)


# Function to display book details
def display_book_details(book_id):
    library = st.session_state.library
    
    try:
        book = library.get_book(book_id)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(book.title)
            st.write(f"**Author:** {book.author}")
            
            if book.year:
                st.write(f"**Year:** {book.year}")
            
            if book.genre:
                st.write(f"**Genre:** {book.genre}")
            
            if book.publisher:
                st.write(f"**Publisher:** {book.publisher}")
            
            if book.pages:
                st.write(f"**Pages:** {book.pages}")
            
            if book.isbn:
                st.write(f"**ISBN:** {book.isbn}")
            
            st.write(f"**Status:** {book.status}")
            st.write(f"**Location:** {book.location}")
            
            if book.rating:
                st.write(f"**Rating:** {'★' * book.rating}{'☆' * (5 - book.rating)}")
            
            if book.tags:
                st.write(f"**Tags:** {', '.join(book.tags)}")
            
            if book.status == "Borrowed":
                st.write(f"**Borrowed by:** {book.borrowed_by}")
                st.write(f"**Borrowed date:** {book.borrowed_date}")
                st.write(f"**Due date:** {book.due_date}")
            
            if book.description:
                st.write("**Description:**")
                st.write(book.description)
        
        with col2:
            # Action buttons
            st.write("**Actions:**")
            
            if st.button("Edit Book", key=f"edit_{book_id}"):
                st.session_state.current_book_id = book_id
                st.session_state.active_tab = "Add/Edit Book"
                st.rerun()
            
            if st.button("Delete Book", key=f"delete_{book_id}"):
                if st.session_state.library.remove_book(book_id):
                    st.session_state.library.save_to_file()
                    st.success(f"Book '{book.title}' removed from library.")
                    st.session_state.show_book_details = False
                    st.rerun()
            
            # Lending/returning actions
            if book.status == "Available":
                if st.button("Lend Book", key=f"lend_{book_id}"):
                    st.session_state.lending_book_id = book_id
                    st.session_state.active_tab = "Lend/Return"
                    st.rerun()
            elif book.status == "Borrowed":
                if st.button("Return Book", key=f"return_{book_id}"):
                    book.return_book()
                    st.session_state.library.save_to_file()
                    st.success(f"Book '{book.title}' has been returned.")
                    st.rerun()
            
            # Tag management
            if st.button("Manage Tags", key=f"tags_{book_id}"):
                st.session_state.tag_book_id = book_id
                st.session_state.active_tab = "Manage Tags"
                st.rerun()
    
    except ValueError as e:
        st.error(f"Error: {e}")


# Function to add or edit a book
def add_edit_book():
    library = st.session_state.library
    
    # Check if we're editing an existing book
    editing = st.session_state.current_book_id is not None
    
    if editing:
        try:
            book = library.get_book(st.session_state.current_book_id)
            st.subheader(f"Edit Book: {book.title}")
        except ValueError:
            st.error("Invalid book ID.")
            st.session_state.current_book_id = None
            return
    else:
        st.subheader("Add New Book")
    
    # Create form for book details
    with st.form("book_form"):
        # Get current values if editing
        current_values = {}
        if editing:
            current_values = {
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "genre": book.genre,
                "year": book.year,
                "publisher": book.publisher,
                "pages": book.pages,
                "description": book.description,
                "location": book.location,
                "rating": book.rating
            }
        
        # Book details inputs
        title = st.text_input("Title*", value=current_values.get("title", ""))
        author = st.text_input("Author*", value=current_values.get("author", ""))
        
        col1, col2 = st.columns(2)
        
        with col1:
            isbn = st.text_input("ISBN", value=current_values.get("isbn", ""))
            genre = st.text_input("Genre", value=current_values.get("genre", ""))
            year = st.number_input("Publication Year", min_value=0, max_value=datetime.datetime.now().year, 
                                  value=current_values.get("year", 0))
            publisher = st.text_input("Publisher", value=current_values.get("publisher", ""))
        
        with col2:
            pages = st.number_input("Number of Pages", min_value=0, value=current_values.get("pages", 0))
            location = st.text_input("Location (e.g., 'Shelf 3')", value=current_values.get("location", "Shelf"))
            rating = st.slider("Rating", min_value=0, max_value=5, value=current_values.get("rating", 0), 
                              help="0 = Not rated")
            
            # Tags input
            if editing:
                tags_input = st.text_input("Tags (comma-separated)", value=", ".join(book.tags))
            else:
                tags_input = st.text_input("Tags (comma-separated)")
        
        description = st.text_area("Description", value=current_values.get("description", ""))
        
        # Submit button
        submit_label = "Update Book" if editing else "Add Book"
        submitted = st.form_submit_button(submit_label)
    
    if submitted:
        # Validate required fields
        if not title:
            st.error("Title is required.")
            return
        
        if not author:
            st.error("Author is required.")
            return
        
        # Process year
        year_value = year if year > 0 else None
        
        # Process pages
        pages_value = pages if pages > 0 else None
        
        # Process rating
        rating_value = rating if rating > 0 else None
        
        # Process tags
        tags_list = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
        tags_list = [tag for tag in tags_list if tag]  # Remove empty tags
        
        try:
            if editing:
                # Update existing book
                library.update_book(
                    st.session_state.current_book_id,
                    title=title,
                    author=author,
                    isbn=isbn,
                    genre=genre,
                    year=year_value,
                    publisher=publisher,
                    pages=pages_value,
                    description=description,
                    location=location,
                    rating=rating_value,
                    tags=tags_list
                )
                st.success(f"Book '{title}' updated successfully.")
            else:
                # Create new book
                new_book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    genre=genre,
                    year=year_value,
                    publisher=publisher,
                    pages=pages_value,
                    description=description,
                    location=location,
                    rating=rating_value,
                    tags=tags_list
                )
                library.add_book(new_book)
                st.success(f"Book '{title}' added to library.")
            
            # Save library and reset current book ID
            library.save_to_file()
            st.session_state.current_book_id = None
            
            # Redirect to library view
            st.session_state.active_tab = "Library"
            st.rerun()
        
        except ValueError as e:
            st.error(f"Error: {e}")
    
    # Cancel button
    if st.button("Cancel"):
        st.session_state.current_book_id = None
        st.session_state.active_tab = "Library"
        st.rerun()


# Function to search books
def search_books():
    library = st.session_state.library
    
    st.subheader("Search Books")
    
    # Search form
    with st.form("search_form"):
        query = st.text_input("Search term")
        
        # Search fields
        st.write("Search in:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_title = st.checkbox("Title", value=True)
            search_author = st.checkbox("Author", value=True)
            search_genre = st.checkbox("Genre", value=True)
        
        with col2:
            search_isbn = st.checkbox("ISBN")
            search_publisher = st.checkbox("Publisher")
            search_description = st.checkbox("Description")
        
        with col3:
            search_tags = st.checkbox("Tags", value=True)
        
        submitted = st.form_submit_button("Search")
    
    if submitted:
        if not query:
            st.warning("Please enter a search term.")
            return
        
        # Determine which fields to search
        fields = []
        if search_title:
            fields.append("title")
        if search_author:
            fields.append("author")
        if search_genre:
            fields.append("genre")
        if search_isbn:
            fields.append("isbn")
        if search_publisher:
            fields.append("publisher")
        if search_description:
            fields.append("description")
        if search_tags:
            fields.append("tags")
        
        # Perform search
        results = library.search_books(query, fields)
        st.session_state.search_results = results
        
        # Display results
        if results:
            st.success(f"Found {len(results)} matching books.")
            df = create_book_dataframe(results)
            
            # Make the dataframe interactive
            st.dataframe(
                df,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        help="Book ID"
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        width="large"
                    ),
                    "Rating": st.column_config.TextColumn(
                        "Rating",
                        width="small"
                    )
                },
                hide_index=True
            )
            
            # Book selection for details
            selected_id = st.selectbox("Select a book to view details:", 
                                      options=results,
                                      format_func=lambda x: f"{library.books[x].title} by {library.books[x].author}")
            
            if st.button("View Book Details"):
                st.session_state.current_book_id = selected_id
                st.session_state.show_book_details = True
                st.rerun()
        else:
            st.info(f"No books found matching '{query}'.")


# Function to filter books
def filter_books():
    library = st.session_state.library
    
    st.subheader("Filter Books")
    
    # Get unique values for select boxes
    genres = [""] + sorted(list(set(book.genre for book in library.books if book.genre)))
    authors = [""] + sorted(list(set(book.author for book in library.books)))
    statuses = ["", "Available", "Borrowed"]
    
    # Filter form
    with st.form("filter_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            status = st.selectbox("Status", options=statuses)
            genre = st.selectbox("Genre", options=genres)
            author = st.selectbox("Author", options=authors)
        
        with col2:
            year_range = st.slider(
                "Publication Year Range",
                min_value=1000,
                max_value=datetime.datetime.now().year,
                value=(1000, datetime.datetime.now().year)
            )
            
            rating_range = st.slider(
                "Rating Range",
                min_value=0,
                max_value=5,
                value=(0, 5)
            )
        
        submitted = st.form_submit_button("Apply Filters")
    
    if submitted:
        # Build filter criteria
        filter_kwargs = {}
        
        if status:
            filter_kwargs["status"] = status
        
        if genre:
            filter_kwargs["genre"] = genre
        
        if author:
            filter_kwargs["author"] = author
        
        if year_range[0] > 1000:
            filter_kwargs["year_from"] = year_range[0]
        
        if year_range[1] < datetime.datetime.now().year:
            filter_kwargs["year_to"] = year_range[1]
        
        if rating_range[0] > 0:
            filter_kwargs["rating_from"] = rating_range[0]
        
        if rating_range[1] < 5:
            filter_kwargs["rating_to"] = rating_range[1]
        
        # Apply filters
        results = library.filter_books(**filter_kwargs)
        st.session_state.filter_results = results
        
        # Display results
        if results:
            st.success(f"Found {len(results)} matching books.")
            df = create_book_dataframe(results)
            
            # Make the dataframe interactive
            st.dataframe(
                df,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        help="Book ID"
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        width="large"
                    ),
                    "Rating": st.column_config.TextColumn(
                        "Rating",
                        width="small"
                    )
                },
                hide_index=True
            )
            
            # Book selection for details
            selected_id = st.selectbox("Select a book to view details:", 
                                      options=results,
                                      format_func=lambda x: f"{library.books[x].title} by {library.books[x].author}")
            
            if st.button("View Book Details"):
                st.session_state.current_book_id = selected_id
                st.session_state.show_book_details = True
                st.rerun()
        else:
            st.info("No books found matching the filter criteria.")


# Function to lend or return books
def lend_return_books():
    library = st.session_state.library
    
    st.subheader("Lend & Return Books")
    
    # Create tabs for lending and returning
    lend_tab, return_tab = st.tabs(["Lend a Book", "Return a Book"])
    
    with lend_tab:
        st.write("Lend a book to someone")
        
        # Get available books
        available_books = library.filter_books(status="Available")
        
        if not available_books:
            st.info("No books available for lending.")
        else:
            # Check if we're coming from a book details page
            if 'lending_book_id' in st.session_state and st.session_state.lending_book_id is not None:
                selected_book = st.session_state.lending_book_id
                st.session_state.lending_book_id = None
            else:
                # Book selection
                selected_book = st.selectbox(
                    "Select a book to lend:",
                    options=available_books,
                    format_func=lambda x: f"{library.books[x].title} by {library.books[x].author}"
                )
            
            # Lending form
            with st.form("lending_form"):
                borrower = st.text_input("Borrower Name")
                days = st.number_input("Lending Period (days)", min_value=1, max_value=365, value=14)
                
                submitted = st.form_submit_button("Lend Book")
                
                if submitted:
                    if not borrower:
                        st.error("Please enter the borrower's name.")
                    else:
                        try:
                            book = library.get_book(selected_book)
                            book.lend(borrower, days)
                            library.save_to_file()
                            st.success(f"Book '{book.title}' has been lent to {borrower}. Due date: {book.due_date}")
                            st.session_state.active_tab = "Library"
                            st.rerun()
                        except ValueError as e:
                            st.error(f"Error: {e}")
    
    with return_tab:
        st.write("Return a borrowed book")
        
        # Get borrowed books
        borrowed_books = library.filter_books(status="Borrowed")
        
        if not borrowed_books:
            st.info("No books are currently borrowed.")
        else:
            # Create a dataframe of borrowed books
            data = []
            for i in borrowed_books:
                book = library.books[i]
                data.append({
                    "ID": i,
                    "Title": book.title,
                    "Author": book.author,
                    "Borrower": book.borrowed_by,
                    "Borrowed Date": book.borrowed_date,
                    "Due Date": book.due_date
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True)
            
            # Book selection for returning
            selected_book = st.selectbox(
                "Select a book to return:",
                options=borrowed_books,
                format_func=lambda x: f"{library.books[x].title} (borrowed by {library.books[x].borrowed_by})"
            )
            
            if st.button("Return Book"):
                try:
                    book = library.get_book(selected_book)
                    book.return_book()
                    library.save_to_file()
                    st.success(f"Book '{book.title}' has been returned.")
                    st.rerun()
                except ValueError as e:
                    st.error(f"Error: {e}")


# Function to manage tags
def manage_tags():
    library = st.session_state.library
    
    st.subheader("Manage Tags")
    
    # Check if we're coming from a book details page
    if 'tag_book_id' in st.session_state and st.session_state.tag_book_id is not None:
        book_id = st.session_state.tag_book_id
        st.session_state.tag_book_id = None
    else:
        # Book selection
        if not library.books:
            st.info("No books in the library.")
            return
        
        book_options = list(range(len(library.books)))
        book_id = st.selectbox(
            "Select a book to manage tags:",
            options=book_options,
            format_func=lambda x: f"{library.books[x].title} by {library.books[x].author}"
        )
    
    try:
        book = library.get_book(book_id)
        st.write(f"Managing tags for: **{book.title}**")
        
        # Current tags
        st.write("Current tags:", ", ".join(book.tags) if book.tags else "None")
        
        # Add tag
        with st.form("add_tag_form"):
            new_tag = st.text_input("Add a new tag")
            add_submitted = st.form_submit_button("Add Tag")
        
        if add_submitted and new_tag:
            book.add_tag(new_tag)
            library.save_to_file()
            st.success(f"Tag '{new_tag}' added.")
            st.rerun()
        
        # Remove tag
        if book.tags:
            with st.form("remove_tag_form"):
                tag_to_remove = st.selectbox("Select tag to remove:", options=book.tags)
                remove_submitted = st.form_submit_button("Remove Tag")
            
            if remove_submitted:
                book.remove_tag(tag_to_remove)
                library.save_to_file()
                st.success(f"Tag '{tag_to_remove}' removed.")
                st.rerun()
            
            # Clear all tags
            if st.button("Clear All Tags"):
                confirm = st.checkbox("Are you sure you want to clear all tags?")
                if confirm:
                    book.tags = []
                    library.save_to_file()
                    st.success("All tags cleared.")
                    st.rerun()
    
    except ValueError as e:
        st.error(f"Error: {e}")


# Function to display library statistics
def display_statistics():
    library = st.session_state.library
    
    st.subheader("Library Statistics")
    
    stats = library.get_statistics()
    
    if stats["total_books"] == 0:
        st.info("Library is empty. No statistics available.")
        return
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Books", stats["total_books"])
    
    with col2:
        st.metric("Available Books", stats["available_books"])
    
    with col3:
        st.metric("Borrowed Books", stats["borrowed_books"])
    
    # Average rating
    if stats["avg_rating"] > 0:
        st.metric("Average Rating", f"{stats['avg_rating']} / 5")
    
    # Oldest and newest books
    if stats["oldest_book"]:
        st.write(f"**Oldest book:** {stats['oldest_book'][0]} ({stats['oldest_book'][1]})")
    
    if stats["newest_book"]:
        st.write(f"**Newest book:** {stats['newest_book'][0]} ({stats['newest_book'][1]})")
    
    # Create tabs for different statistics
    genre_tab, author_tab, year_tab, rating_tab, tag_tab = st.tabs([
        "Genres", "Authors", "Publication Years", "Ratings", "Tags"
    ])
    
    # Genre statistics
    with genre_tab:
        if stats["genres"]:
            st.subheader("Books by Genre")
            
            # Create dataframe for genres
            genre_data = pd.DataFrame({
                "Genre": list(stats["genres"].keys()),
                "Count": list(stats["genres"].values())
            }).sort_values("Count", ascending=False)
            
            # Create bar chart
            fig = px.bar(
                genre_data,
                x="Genre",
                y="Count",
                title="Books by Genre",
                color="Count",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig)
        else:
            st.info("No genre information available.")
    
    # Author statistics
    with author_tab:
        if stats["authors"]:
            st.subheader("Books by Author")
            
            # Limit to top 10 authors
            author_data = pd.DataFrame({
                "Author": list(stats["authors"].keys()),
                "Count": list(stats["authors"].values())
            }).sort_values("Count", ascending=False).head(10)
            
            # Create bar chart
            fig = px.bar(
                author_data,
                x="Author",
                y="Count",
                title="Top 10 Authors",
                color="Count",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig)
        else:
            st.info("No author information available.")
    
    # Publication year statistics
    with year_tab:
        if stats["years"]:
            st.subheader("Books by Publication Year")
            
            # Create dataframe for years
            year_data = pd.DataFrame({
                "Year": list(stats["years"].keys()),
                "Count": list(stats["years"].values())
            }).sort_values("Year")
            
            # Create line chart
            fig = px.line(
                year_data,
                x="Year",
                y="Count",
                title="Books by Publication Year",
                markers=True
            )
            st.plotly_chart(fig)
        else:
            st.info("No publication year information available.")
    
    # Rating statistics
    with rating_tab:
        st.subheader("Books by Rating")
        
        # Create dataframe for ratings
        rating_data = pd.DataFrame({
            "Rating": ["★" * i if i > 0 else "Unrated" for i in range(6)],
            "Count": [stats["ratings"][i] if i > 0 else stats["ratings"]["unrated"] for i in range(6)]
        })
        
        # Create bar chart
        fig = px.bar(
            rating_data,
            x="Rating",
            y="Count",
            title="Books by Rating",
            color="Count",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig)
    
    # Tag statistics
    with tag_tab:
        if stats["tags"]:
            st.subheader("Most Common Tags")
            
            # Limit to top 15 tags
            tag_data = pd.DataFrame({
                "Tag": list(stats["tags"].keys()),
                "Count": list(stats["tags"].values())
            }).sort_values("Count", ascending=False).head(15)
            
            # Create bar chart
            fig = px.bar(
                tag_data,
                x="Tag",
                y="Count",
                title="Top 15 Tags",
                color="Count",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig)
        else:
            st.info("No tag information available.")


# Function to handle library settings
def library_settings():
    library = st.session_state.library
    
    st.subheader("Library Settings")
    
    # Library name
    with st.form("library_name_form"):
        current_name = library.name
        st.write(f"Current library name: **{current_name}**")
        
        new_name = st.text_input("New Library Name")
        name_submitted = st.form_submit_button("Change Name")
    
    if name_submitted:
        if new_name:
            library.name = new_name
            library.save_to_file()
            st.success(f"Library name changed to: {new_name}")
            st.rerun()
        else:
            st.error("Library name cannot be empty.")
    
    # Save/load library
    st.write("---")
    st.subheader("Save/Load Library")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("save_form"):
            save_path = st.text_input("Save Path", value=library.file_path)
            save_submitted = st.form_submit_button("Save Library")
        
        if save_submitted:
            try:
                library.save_to_file(save_path)
                st.success(f"Library saved to: {save_path}")
            except Exception as e:
                st.error(f"Error saving library: {e}")
    
    with col2:
        with st.form("load_form"):
            load_path = st.text_input("Load Path", value=library.file_path)
            load_submitted = st.form_submit_button("Load Library")
        
        if load_submitted:
            try:
                library.load_from_file(load_path)
                st.success(f"Library loaded from: {load_path}")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading library: {e}")
    
    # Export library
    st.write("---")
    st.subheader("Export Library")
    
    export_format = st.selectbox("Export Format", ["CSV", "Excel"])
    
    if st.button("Export"):
        if not library.books:
            st.error("Library is empty. Nothing to export.")
        else:
            # Create dataframe for export
            data = []
            for i, book in enumerate(library.books):
                data.append({
                    "Title": book.title,
                    "Author": book.author,
                    "ISBN": book.isbn,
                    "Genre": book.genre,
                    "Year": book.year,
                    "Publisher": book.publisher,
                    "Pages": book.pages,
                    "Description": book.description,
                    "Location": book.location,
                    "Status": book.status,
                    "Rating": book.rating,
                    "Date Added": book.date_added,
                    "Tags": ", ".join(book.tags),
                    "Borrowed By": book.borrowed_by,
                    "Borrowed Date": book.borrowed_date,
                    "Due Date": book.due_date
                })
            
            df = pd.DataFrame(data)
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="library_export.csv",
                    mime="text/csv"
                )
            else:  # Excel
                # For Excel, we need to use a BytesIO object
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Library', index=False)
                
                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name="library_export.xlsx",
                    mime="application/vnd.ms-excel"
                )


# Main function
def main():
    # Set page config
    st.set_page_config(
        page_title="Personal Library Manager",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # App title
    st.title("📚 Personal Library Manager")
    
    # Display library name
    st.write(f"**Library:** {st.session_state.library.name}")
    
    # Create tabs for different sections
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Library"
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Navigation buttons
    if st.sidebar.button("Library", use_container_width=True):
        st.session_state.active_tab = "Library"
        st.session_state.show_book_details = False
        st.rerun()
    
    if st.sidebar.button("Add New Book", use_container_width=True):
        st.session_state.active_tab = "Add/Edit Book"
        st.session_state.current_book_id = None
        st.rerun()
    
    if st.sidebar.button("Search Books", use_container_width=True):
        st.session_state.active_tab = "Search"
        st.rerun()
    
    if st.sidebar.button("Filter Books", use_container_width=True):
        st.session_state.active_tab = "Filter"
        st.rerun()
    
    if st.sidebar.button("Lend/Return Books", use_container_width=True):
        st.session_state.active_tab = "Lend/Return"
        st.rerun()
    
    if st.sidebar.button("Manage Tags", use_container_width=True):
        st.session_state.active_tab = "Manage Tags"
        st.rerun()
    
    if st.sidebar.button("Statistics", use_container_width=True):
        st.session_state.active_tab = "Statistics"
        st.rerun()
    
    if st.sidebar.button("Settings", use_container_width=True):
        st.session_state.active_tab = "Settings"
        st.rerun()
    
    # Display library stats in sidebar
    st.sidebar.write("---")
    st.sidebar.subheader("Quick Stats")
    
    stats = st.session_state.library.get_statistics()
    st.sidebar.write(f"Total Books: {stats['total_books']}")
    st.sidebar.write(f"Available: {stats['available_books']}")
    st.sidebar.write(f"Borrowed: {stats['borrowed_books']}")
    
    if stats['avg_rating'] > 0:
        st.sidebar.write(f"Avg Rating: {stats['avg_rating']} / 5")
    
    # Main content based on active tab
    if st.session_state.show_book_details and st.session_state.current_book_id is not None:
        display_book_details(st.session_state.current_book_id)
    elif st.session_state.active_tab == "Library":
        # Library view
        st.subheader("My Library")
        
        # Add book button
        if st.button("Add New Book"):
            st.session_state.active_tab = "Add/Edit Book"
            st.session_state.current_book_id = None
            st.rerun()
        
        # Display books
        if not st.session_state.library.books:
            st.info("Your library is empty. Add some books to get started!")
        else:
            df = create_book_dataframe()
            
            # Make the dataframe interactive
            st.dataframe(
                df,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        help="Book ID"
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        width="large"
                    ),
                    "Rating": st.column_config.TextColumn(
                        "Rating",
                        width="small"
                    )
                },
                hide_index=True
            )
            
            # Book selection for details
            book_id = st.selectbox(
                "Select a book to view details:",
                options=range(len(st.session_state.library.books)),
                format_func=lambda x: f"{st.session_state.library.books[x].title} by {st.session_state.library.books[x].author}"
            )
            
            if st.button("View Book Details"):
                st.session_state.current_book_id = book_id
                st.session_state.show_book_details = True
                st.rerun()
    
    elif st.session_state.active_tab == "Add/Edit Book":
        add_edit_book()
    
    elif st.session_state.active_tab == "Search":
        search_books()
    
    elif st.session_state.active_tab == "Filter":
        filter_books()
    
    elif st.session_state.active_tab == "Lend/Return":
        lend_return_books()
    
    elif st.session_state.active_tab == "Manage Tags":
        manage_tags()
    
    elif st.session_state.active_tab == "Statistics":
        display_statistics()
    
    elif st.session_state.active_tab == "Settings":
        library_settings()


if __name__ == "__main__":
    main()