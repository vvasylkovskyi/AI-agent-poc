import wikipedia


# Equivalent of the search_wikipedia function
def search_wikipedia(search_query):
    # Fetch the page content

    try:
        page = wikipedia.page(search_query)
        # Extract the text
        text = page.content

        # Print and return the first 100 characters
        return text[:300]
    except wikipedia.exceptions.PageError:
        return "Page not found for the search query: {search_query}"
