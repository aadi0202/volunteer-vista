# VolunteerVista

VolunteerVista is a Flask-based web application that connects NGOs with potential volunteers, facilitating communication and collaboration for social impact initiatives.

## Features

### For NGOs
- Create and manage organizational profiles
- Review volunteer applications
- Real-time chat with potential volunteers
- Dashboard to track volunteer engagement
- Custom logo upload and profile management

### For Volunteers
- Create detailed volunteer profiles
- Browse and apply to NGO opportunities
- Track application status
- Real-time chat with NGOs
- Profile customization with photo upload

### For Administrators
- User management (NGOs and Volunteers)
- Content moderation
- System configuration
- Monitor chat logs
- Manage join requests
- Post system-wide announcements

### General Features
- Real-time notifications
- Secure authentication
- Profile image management
- Search functionality
- Responsive design

## Technical Stack

- **Backend Framework:** Flask
- **Database:** SQLite (with SQLAlchemy ORM)
- **Real-time Communication:** Flask-SocketIO
- **File Management:** Werkzeug
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** Flask Session Management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aadi0202/volunteer-vista.git
cd volunteervista
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add:
```
SECRET_KEY=your_secret_key_here
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
python app.py
```

## Project Structure

```
volunteervista/
├── static/
│   ├── uploads/       # User uploaded files
│   └── images/        # Static images
│   └── css/           # Main stylesheet
├── templates/         # HTML templates
├── app.py             # Main application file
├── requirements.txt   # Project dependencies
```

## Database Models

- **NGO:** Organization profiles and authentication
- **Volunteer:** Volunteer profiles and authentication
- **JoinRequest:** Manages volunteer applications to NGOs
- **Conversation:** Handles chat functionality
- **Message:** Stores chat messages
- **Admin:** Administrator accounts
- **SystemConfig:** Global system settings
- **Notification:** User notifications

## Routes

### Admin Routes
- `/admin/login` - Admin authentication
- `/admin/dashboard` - Admin control panel
- `/admin/users` - User management
- `/admin/system_config` - System settings
- `/admin/content_moderation` - Content monitoring

### NGO Routes
- `/ngo/login` - NGO authentication
- `/ngo/signup` - New NGO registration
- `/ngo/dashboard` - NGO control panel
- `/ngo/edit` - Profile management

### Volunteer Routes
- `/volunteer/login` - Volunteer authentication
- `/volunteer/signup` - New volunteer registration
- `/volunteer/dashboard` - Volunteer dashboard
- `/volunteer/edit` - Profile management

### Chat Routes
- `/chat/<partner_email>` - Individual chat sessions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Considerations

- All uploaded files are securely handled using `secure_filename`
- Session-based authentication implementation
- Password storage (Note: Currently stored as plaintext - should be hashed in production)
- Input validation and sanitization
- CSRF protection through Flask's built-in security features

## Future Enhancements

- More details for the registration of ngo
- Implement password hashing
- Add email verification
- Integrate with external authentication providers
- Add advanced search filters
- Implement a rating/review system
- Add volunteer opportunity posting system
- Integrate with calendar for scheduling
- Add data analytics dashboard

## Connect With Me 🌐

- 💼 LinkedIn: [Aaditya Punatar](https://www.linkedin.com/in/aaditya-punatar/)
- 🐱 GitHub: [@aadi0202](https://github.com/aadi0202)
- 📧 Email: aadipunatar@gmail.com
- 🌐 Website: [aadityapunatar.me](https://aadityapunatar.me)
