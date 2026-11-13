# Research Paper Management System (RPMS)

RPMS is a Django-based web application for managing research paper submissions, reviewer assignments, review progress, and final publication decisions.

The system provides separate dashboards and permissions for Admins, Authors, and Reviewers.

## Main Features

- Author registration and login
- Role-based access control
- Separate Admin, Author, and Reviewer dashboards
- Conference and journal management
- Research paper submission with PDF upload
- Paper-version storage
- Initial paper screening
- Reviewer assignment
- Reviewer acceptance and decline workflow
- Review completion with acceptance or rejection recommendation
- Final paper acceptance or rejection
- Submission-status tracking
- Automated Django tests
- Environment-variable configuration

## User Roles

### Admin

The Admin can:

- Create and manage conferences and journals
- View submitted research papers
- Perform initial paper screening
- Assign papers to Reviewers
- Track reviewer-assignment progress
- View reviewer recommendations
- Accept or reject papers

### Author

The Author can:

- Register for an account
- Log in to the Author dashboard
- View available conferences and journals
- Submit research papers as PDF files
- View their own submissions
- Track paper status and final decisions

### Reviewer

The Reviewer can:

- Log in to the Reviewer dashboard
- View assigned research papers
- Accept or decline assignments
- Open uploaded paper files
- Complete accepted assignments
- Recommend acceptance or rejection

## Paper Workflow

```text
Author submits paper
        ↓
Admin performs initial screening
        ↓
Paper becomes ready for reviewer assignment
        ↓
Admin assigns a Reviewer
        ↓
Reviewer accepts or declines
        ↓
Reviewer completes the review
        ↓
Reviewer recommends Accept or Reject
        ↓
Admin makes the final decision
        ↓
Author sees Accepted or Rejected status
```

## Technologies Used

- Python
- Django 6.0.6
- SQLite
- HTML
- CSS
- Bootstrap 5
- JavaScript
- python-dotenv 1.2.2

## Authentication

The current application uses Django session authentication.

JWT authentication and a REST API are not currently implemented. They may be added as future extensions for mobile applications, separate frontend applications, or external integrations.

## Project Setup

### 1. Clone the repository

```powershell
git clone <repository-url>
cd RPMS
```

Replace `<repository-url>` with the actual GitHub repository URL.

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Create the environment file

Copy `.env.example` and rename the copied file to `.env`.

In PowerShell:

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain:

```env
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_TIME_ZONE=Asia/Kathmandu
```

Generate a secure Django secret key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key and place it in `.env`:

```env
DJANGO_SECRET_KEY=paste-the-generated-key-here
```

Do not place the real secret key inside `.env.example`.

### 4. Apply database migrations

```powershell
python manage.py migrate
```

This creates the local SQLite database and all required tables.

### 5. Create a superuser

```powershell
python manage.py createsuperuser
```

Enter the requested username, email, and password.

After creating the superuser, open the Django administration interface and make sure the user has the RPMS Admin role.

### 6. Start the development server

```powershell
python manage.py runserver
```

Open the application in a browser:

```text
http://127.0.0.1:8000/
```

Open the Django administration interface:

```text
http://127.0.0.1:8000/admin/
```

## Running Automated Tests

Run the complete test suite:

```powershell
python manage.py test
```

The project currently contains 58 automated tests covering:

- Author registration
- Login behavior
- Role-based dashboard access
- Publication management
- Publication deadline validation
- Paper submission
- PDF validation
- Paper-version creation
- Author submission ownership
- Admin paper management
- Initial paper screening
- Reviewer assignment
- Reviewer accept and decline behavior
- Review recommendations
- Paper-status updates
- Final acceptance and rejection rules

Run tests for an individual Django app:

```powershell
python manage.py test accounts
python manage.py test dashboard
python manage.py test publications
python manage.py test papers
python manage.py test reviews
```

## System Check

Run Django's system check with:

```powershell
python manage.py check
```

A successful result should display:

```text
System check identified no issues (0 silenced).
```

## Environment Variables

The following environment variables are used:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django cryptographic secret key |
| `DJANGO_DEBUG` | Enables or disables debug mode |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DJANGO_TIME_ZONE` | Application time zone |

The real `.env` file is excluded from Git and must remain private.

The `.env.example` file contains safe placeholder values and can be committed to GitHub.

## Database

The current project uses SQLite for local development.

The local database file is:

```text
db.sqlite3
```

This file is excluded from Git because it can contain:

- Local user accounts
- Password hashes
- Test records
- Mock publications
- Submitted paper information
- Local development data

The database structure is preserved through Django migration files.

After cloning the project, recreate the database with:

```powershell
python manage.py migrate
```

## Uploaded Media

Uploaded research papers are stored in the `media/` directory during local development.

The `media/` directory is excluded from Git because uploaded papers may contain private or temporary files.

## Files Excluded from Git

The `.gitignore` file excludes local and sensitive files such as:

```text
.env
db.sqlite3
media/
staticfiles/
__pycache__/
.vscode/
.idea/
```

Django migration files should remain included in Git.

## Project Structure

```text
RPMS/
├── accounts/
├── config/
├── dashboard/
├── papers/
├── publications/
├── reviews/
├── static/
├── templates/
├── .env.example
├── .gitignore
├── manage.py
├── README.md
└── requirements.txt
```

## Main Django Apps

### `accounts`

Contains:

- Custom User model
- User roles
- Author registration
- Login and logout behavior

### `dashboard`

Contains:

- Home page
- Role-based dashboard redirection
- Admin dashboard
- Author dashboard
- Reviewer dashboard
- Role-access decorator

### `publications`

Contains:

- Conference and journal model
- Publication creation and management
- Publication deadline validation
- Available-publication filtering

### `papers`

Contains:

- Research paper model
- Paper-version model
- PDF submission
- Author submission tracking
- Initial screening
- Final decisions

### `reviews`

Contains:

- Reviewer assignments
- Reviewer accept and decline actions
- Review completion
- Acceptance and rejection recommendations
- Review-status updates

## Paper Statuses

RPMS uses the following paper statuses:

- Draft
- Submitted
- Under Initial Review
- Ready for Reviewer Assignment
- Under Review
- Review Completed
- Revision Required
- Accepted
- Rejected

## Reviewer Assignment Statuses

Reviewer assignments use the following statuses:

- Assigned
- Accepted
- Declined
- Completed

A completed assignment contains one of these recommendations:

- Recommend Accept
- Recommend Reject

The recommendation does not automatically decide the paper. The Admin makes the final decision.

## Current Project Scope

The current RPMS project focuses on six main features:

1. Author registration
2. Paper submission
3. Reviewer assignment
4. Review tracking
5. Acceptance and rejection workflow
6. Conference and journal management

## Future Improvements

Possible future improvements include:

- Django REST Framework API
- JWT authentication for API clients
- Separate React or mobile frontend
- Email notifications
- Paper revision and resubmission workflow
- Reviewer comments and scoring
- Search and filtering
- Pagination
- PostgreSQL support
- Cloud file storage
- Production deployment
- Mobile UI testing and improvements

## Security Notes

- Never commit the real `.env` file.
- Never commit a real Django secret key.
- Do not use `DEBUG=True` in production.
- Configure production hosts using `DJANGO_ALLOWED_HOSTS`.
- Uploaded research papers should not be made publicly accessible without proper permission checks.
- Use secure database and deployment credentials in production.

## Development Status

The main RPMS workflows, desktop interface, security configuration, and automated tests are complete.

The project currently passes:

```text
58 automated tests
Django system check with no issues
```