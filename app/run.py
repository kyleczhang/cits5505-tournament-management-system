from criktrack import create_app

app = create_app()

# debug is always True here, so don't use the Flask development server in production. Use a production WSGI
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
