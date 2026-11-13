# Research Paper Management System (RPMS)

RPMS is a Django-based web application for managing the complete research paper publication workflow, from initial manuscript submission through peer review, revision, editorial decision, copyediting, production, and final publication.

The system supports separate role-based workflows for Journal Owners, Editors, Authors, and Reviewers, while Django superusers act as technical System Administrators.

## Main Features

- Author registration and authentication
- Role-based dashboards and access control
- Journal and conference management
- Journal Owner account isolation
- Editor and Reviewer account management
- Multiple Editors per Journal or Conference
- Research paper submission with PDF upload
- Secure paper-version access
- Initial paper screening
- Multiple Reviewers per paper
- Review Round management
- Paper Version tracking
- Reviewer acceptance and decline workflow
- Reviewer comments and recommendations
- Revision requests and Author resubmission
- Reuse of the same Reviewer in later Review Rounds
- Final acceptance or rejection by the Editor
- Copyediting workflow
- Optional Author correction during copyediting
- Production workflow
- Final publication
- Review deadline and overdue tracking
- Publication submission-date tracking
- Automated Django tests
- Environment-variable configuration

## User Roles

### System Administrator

The technical System Administrator is a Django superuser.

The System Administrator can:

- Access the Django administration interface
- Manage system-level data
- Create Journal Owner accounts
- Perform technical administration of the application

The System Administrator is separate from the normal RPMS business roles.

### Journal Owner

A Journal Owner represents the publisher or organization responsible for Journals and Conferences.

The Journal Owner can:

- Create and manage multiple Journals and Conferences
- Configure publication details and submission deadlines
- Create Editor and Reviewer accounts
- View only Editors and Reviewers belonging to their own environment
- Assign one or multiple Editors to a Journal or Conference
- Monitor papers submitted to owned publications
- View review and editorial progress
- Start the production process for papers ready for production
- Publish completed papers

Each Journal Owner operates independently. Editors and Reviewers created by one Journal Owner cannot be assigned to another Journal Owner's publications.

### Editor

The Editor manages the editorial workflow for assigned Journals and Conferences.

The Editor can:

- View papers submitted to assigned publications
- Perform initial paper screening
- Mark papers ready for peer review
- Assign one or multiple Reviewers
- Manage Review Rounds
- Track Reviewer responses and recommendations
- View current and previous review history
- Make the official final acceptance or rejection decision
- Start copyediting for accepted papers
- Complete copyediting directly when no correction is required
- Request copyediting corrections from the Author
- Review corrected manuscripts
- Complete copyediting and send papers to production

Reviewer recommendations do not automatically determine the final paper decision. The assigned Editor makes the official final decision.

### Author

Authors are independent public users and are not owned by a Journal Owner.

The Author can:

- Register for an account
- Log in to the Author dashboard
- View currently available Journals and Conferences
- Submit research papers as PDF files
- View their own submissions
- Track paper progress
- View Reviewer feedback without seeing Reviewer identity
- Upload revised manuscript versions when revision is requested
- View previous manuscript versions and Review Rounds
- View the final editorial decision
- Respond to copyediting correction requests
- Upload corrected manuscript versions
- Track papers through production and publication

### Reviewer

The Reviewer participates in peer-review assignments created by Editors.

The Reviewer can:

- Log in to the Reviewer dashboard
- View only their own review assignments
- View the exact Paper Version assigned to a Review Round
- Accept or decline review assignments
- Submit review comments
- Recommend acceptance
- Recommend rejection
- Request revision
- Participate in later Review Rounds when reassigned

The same Reviewer can be assigned again to a later Review Round after the Author submits a revised version.

## Complete Paper Workflow

```text
Journal Owner creates a Journal or Conference
        ↓
Journal Owner assigns Editor(s)
        ↓
Author submits Paper Version 1
        ↓
Editor performs initial screening
        ↓
Paper becomes ready for Reviewer assignment
        ↓
Editor assigns one or multiple Reviewers
        ↓
Reviewer accepts or declines the assignment
        ↓
Reviewer reviews the assigned Paper Version
        ↓
Reviewer chooses one recommendation:
    - Recommend Accept
    - Recommend Reject
    - Request Revision
        ↓
If Revision is requested:
        ↓
Author views Reviewer feedback
        ↓
Author uploads a revised Paper Version
        ↓
A new Review Round is created
        ↓
Editor assigns Reviewer(s) again
        ↓
Peer review continues
        ↓
Review Round is completed
        ↓
Editor makes the official final decision
        ↓
Accepted or Rejected
        ↓
If Accepted:
        ↓
Editor starts Copyediting
        ↓
Editor either:
    - Completes Copyediting directly
      OR
    - Requests Author Correction
        ↓
If correction is requested:
        ↓
Author uploads corrected manuscript
        ↓
Editor completes Copyediting
        ↓
Paper becomes Ready for Production
        ↓
Journal Owner starts Production
        ↓
Paper becomes In Production
        ↓
Journal Owner publishes the Paper
        ↓
Published
```

## Publication Management

RPMS supports two publication types:

- Journal
- Conference

### Journal Information

Journal publications can contain:

- ISSN
- Volume
- Issue
- Publication frequency
- Submission opening date
- Submission deadline
- Review deadline

### Conference Information

Conference publications can contain:

- Organizer
- Venue
- Event date
- Location
- Submission opening date
- Submission deadline
- Review deadline

## Publication Lifecycle

Publications use the following lifecycle states:

- Draft
- Active
- Archived

Submission availability is calculated separately from the publication lifecycle.

The submission state can be:

- Upcoming
- Open for Submission
- Closed for Submission

An Author can submit only when the publication is active and the current date is inside the configured submission period.

## Paper Statuses

RPMS currently uses the following paper statuses:

- Draft
- Submitted
- Under Initial Review
- Ready for Reviewer Assignment
- Under Review
- Review Completed
- Revision Required
- Accepted
- Rejected
- Copyediting
- Copyediting Correction Required
- Ready for Production
- In Production
- Published

## Review Rounds

Each peer-review cycle is stored as a separate Review Round.

Review Round statuses are:

- Open
- Revision Required
- Completed

Each Review Round is connected to one specific Paper Version.

For example:

```text
Paper Version 1
        ↓
Review Round 1
        ↓
Revision Requested
        ↓
Paper Version 2
        ↓
Review Round 2
```

This preserves the complete review history instead of replacing previous review information.

## Reviewer Assignment Statuses

Reviewer assignments use the following statuses:

- Assigned
- Accepted
- Declined
- Completed

A completed review can contain one of the following recommendations:

- Recommend Accept
- Recommend Reject
- Request Revision

Reviewer recommendations are advisory. The Editor makes the official final paper decision.

## Copyediting Workflow

After a paper is accepted, the Editor can start copyediting.

Copyediting statuses are:

- In Progress
- Correction Required
- Correction Submitted
- Completed

The Editor has two possible paths.

### No Correction Required

```text
Accepted
    ↓
Copyediting
    ↓
Complete Copyediting
    ↓
Ready for Production
```

### Author Correction Required

```text
Accepted
    ↓
Copyediting
    ↓
Editor requests correction
    ↓
Author uploads corrected version
    ↓
Correction Submitted
    ↓
Editor completes Copyediting
    ↓
Ready for Production
```

## Production Workflow

Production is managed by the Journal Owner.

Production statuses are:

- In Production
- Published

The workflow is:

```text
Ready for Production
        ↓
Journal Owner starts Production
        ↓
In Production
        ↓
Journal Owner publishes Paper
        ↓
Published
```

The system records who started production, who published the paper, and the corresponding timestamps.

## Technologies Used

- Python 3.14
- Django 6.0.6
- SQLite
- HTML
- CSS
- Bootstrap 5
- JavaScript
- python-dotenv 1.2.2

## Authentication

RPMS currently uses Django session authentication.

Public registration is available for Authors.

Editor and Reviewer accounts are created by their Journal Owner.

Journal Owner accounts are created by the technical System Administrator through Django Admin.

JWT authentication and a REST API are not currently implemented. They may be added later for mobile applications, separate frontend applications, or external integrations.

## Access Isolation

RPMS implements account and publication isolation.

### Journal Owner Isolation

A Journal Owner can access only:

- Their own Journals and Conferences
- Editors created by that Journal Owner
- Reviewers created by that Journal Owner
- Papers submitted to publications owned by that Journal Owner

### Editor Isolation

Editors can manage papers only for publications to which they have been assigned.

### Reviewer Isolation

Reviewers can access only their own assignments and only the Paper Versions connected to those assignments.

### Author Isolation

Authors can access only their own paper submissions, revisions, feedback, decisions, and publication progress.

## Secure Paper Files

Uploaded research papers are not exposed through public media URLs.

Paper files are accessed through a protected Django view that verifies the logged-in user's permission.

Access can be granted to:

- The Paper's Author
- Editors assigned to the publication
- The Journal Owner of the publication
- Reviewers assigned to the specific Review Round and Paper Version
- Django superusers

Unauthorized file requests return a `404` response.

Direct Django development serving of `/media/` URLs is not enabled.

## PDF Validation

Manuscript uploads are validated before they are accepted.

The system verifies:

- `.pdf` file extension
- Maximum file size of 10 MB
- PDF file signature

The validation is used for:

- Initial paper submission
- Revised paper submission
- Copyediting correction submission

## Project Setup

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd RPMS
```

Replace `<repository-url>` with the actual GitHub repository URL.

### 2. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

Current dependencies are:

```text
Django==6.0.6
python-dotenv==1.2.2
```

### 3. Create the Environment File

Copy `.env.example` and rename the copied file to `.env`.

Using PowerShell:

```powershell
Copy-Item .env.example .env
```

The `.env` file uses:

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

Copy the generated key into:

```env
DJANGO_SECRET_KEY=paste-the-generated-key-here
```

Never place the real secret key inside `.env.example`.

### 4. Apply Database Migrations

```powershell
python manage.py migrate
```

This creates the local SQLite database and required tables.

### 5. Create the System Administrator

```powershell
python manage.py createsuperuser
```

Enter the requested username, email, and password.

The created Django superuser acts as the technical System Administrator.

The superuser does not need to be assigned a normal RPMS business role.

### 6. Create a Journal Owner

Start the development server and log in to Django Admin:

```text
http://127.0.0.1:8000/admin/
```

Create a normal RPMS user with the role:

```text
Journal Owner
```

The Journal Owner can then create Editor and Reviewer accounts from the RPMS interface.

### 7. Start the Development Server

```powershell
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

Django Admin is available at:

```text
http://127.0.0.1:8000/admin/
```

## Running Automated Tests

Run the complete test suite:

```powershell
python manage.py test
```

The current project contains:

```text
91 automated tests
```

The test suite covers important areas including:

- User registration
- Authentication
- Role-based dashboard access
- Journal Owner access
- Editor access
- Reviewer access
- Author access
- Publication management
- Publication ownership isolation
- Editor account isolation
- Publication deadline validation
- Available-publication filtering
- Paper submission
- PDF validation
- Paper Version creation
- Author submission ownership
- Initial screening
- Reviewer assignment
- Reviewer account isolation
- Multiple Reviewer behavior
- Review Round behavior
- Reviewer acceptance
- Reviewer decline
- Reviewer recommendations
- Revision requests
- Reviewer reuse in later Review Rounds
- Final editorial decisions
- Protected Paper Version access
- Copyediting workflow
- Copyediting correction workflow

Run tests for an individual Django app with:

```powershell
python manage.py test accounts
python manage.py test dashboard
python manage.py test publications
python manage.py test papers
python manage.py test reviews
```

The current full test-suite result is:

```text
Found 91 test(s).
System check identified no issues (0 silenced).
Ran 91 tests
OK
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

RPMS uses the following environment variables:

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

The database is excluded from Git because it may contain:

- Local user accounts
- Password hashes
- Test records
- Publication records
- Submitted paper information
- Local development data

The database structure is preserved through Django migration files.

After cloning the repository, recreate the database structure with:

```powershell
python manage.py migrate
```

## Uploaded Media

Uploaded paper files are stored inside the local:

```text
media/
```

directory.

The `media/` directory is excluded from Git because manuscripts can contain private or temporary research material.

Application users access paper files through protected RPMS routes rather than direct public media URLs.

## Files Excluded from Git

The `.gitignore` file excludes local or sensitive files such as:

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
- RPMS user roles
- Author registration
- Login and logout
- Journal Owner managed accounts
- Editor and Reviewer account creation
- Owner-based account isolation

### `dashboard`

Contains:

- Public home page
- Role-based dashboard redirection
- Journal Owner dashboard
- Editor dashboard
- Author dashboard
- Reviewer dashboard
- Role-access decorators

Django superusers are redirected to Django Admin instead of a normal RPMS dashboard.

### `publications`

Contains:

- Journal and Conference models
- Journal-specific information
- Conference-specific information
- Publication ownership
- Editor assignment
- Publication lifecycle
- Submission availability
- Publication deadline validation
- Journal Owner isolation
- Available-publication filtering for Authors

### `papers`

Contains:

- Research Paper model
- Paper Version model
- PDF submission and validation
- Initial screening
- Author revision upload
- Paper history
- Final Decision
- Copyediting
- Copyediting corrections
- Production
- Publication
- Protected Paper Version access

### `reviews`

Contains:

- Review Round model
- Reviewer Assignment model
- Multiple Reviewer support
- Reviewer acceptance and decline
- Reviewer comments
- Accept recommendation
- Reject recommendation
- Revision recommendation
- Review Round completion
- Reviewer reuse across later rounds
- Reviewer account isolation

## Current Project Scope

The current RPMS implementation covers the complete research publication workflow:

1. Author registration
2. Journal and Conference management
3. Editor and Reviewer account management
4. Paper submission
5. Initial editorial screening
6. Reviewer assignment
7. Multiple Reviewer support
8. Review Round tracking
9. Reviewer comments and recommendations
10. Revision and resubmission
11. Paper Version tracking
12. Final acceptance or rejection
13. Copyediting
14. Optional Author copyediting correction
15. Production
16. Final publication
17. Role and account isolation
18. Secure manuscript access

## Future Improvements

Possible future improvements include:

- Django REST Framework API
- JWT authentication for API clients
- Email notifications
- Search and advanced filtering
- Pagination for larger datasets
- Reviewer scoring or structured review forms
- PostgreSQL deployment configuration
- Cloud file storage
- Production server deployment
- Audit logs
- Publication analytics
- DOI or external publishing-service integration
- Separate mobile or frontend application
- Additional mobile UI testing

## Security Notes

- Never commit the real `.env` file.
- Never commit a real Django secret key.
- Never commit the local `db.sqlite3` database.
- Do not commit private manuscript files.
- Do not use `DEBUG=True` in production.
- Configure production hosts through `DJANGO_ALLOWED_HOSTS`.
- Use HTTPS in production.
- Use secure production database credentials.
- Keep manuscript access behind permission checks.
- Journal Owner, Editor, Reviewer, and Author access should remain isolated.

## Development Status

The main RPMS V2 workflow is implemented and functional.

The complete workflow has been verified from:

```text
Author Submission
→ Initial Screening
→ Reviewer Assignment
→ Peer Review
→ Revision
→ New Paper Version
→ New Review Round
→ Final Editorial Decision
→ Copyediting
→ Author Correction
→ Ready for Production
→ Production
→ Published
```

Current verification status:

```text
91 automated tests passed
Django system check passed with no issues
Full end-to-end publication workflow verified
```