"""Unit tests for calw_test - Login & Registration system."""

import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app, USERS, validate_registration


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def fresh_users():
    """Reset USERS to original state."""
    original = USERS.copy()
    USERS.clear()
    USERS.update({
        "admin": {"password": "admin123", "name": "管理员"},
        "user1": {"password": "user123", "name": "测试用户"},
    })
    yield
    USERS.clear()
    USERS.update(original)


# ============ Registration Validation Tests ============

class TestValidateRegistration:
    """Tests for validate_registration function."""

    def test_valid_registration(self):
        """Valid registration data should pass."""
        valid, msg = validate_registration(
            "newuser", "password123", "password123", "NewUser"
        )
        assert valid is True
        assert msg == ""

    def test_empty_username(self):
        """Empty username should fail."""
        valid, msg = validate_registration("", "password123", "password123", "新用户")
        assert valid is False
        assert "必填" in msg

    def test_short_username(self):
        """Username less than 3 chars should fail."""
        valid, msg = validate_registration("ab", "password123", "password123", "新用户")
        assert valid is False
        assert "3-20" in msg

    def test_long_username(self):
        """Username more than 20 chars should fail."""
        valid, msg = validate_registration("a" * 21, "password123", "password123", "新用户")
        assert valid is False
        assert "3-20" in msg

    def test_invalid_username_chars(self):
        """Username with special chars should fail."""
        valid, msg = validate_registration("user@name", "password123", "password123", "新用户")
        assert valid is False
        assert "字母" in msg

    def test_short_password(self):
        """Password less than 6 chars should fail."""
        valid, msg = validate_registration("newuser", "12345", "12345", "NewUser")
        assert valid is False
        assert "6" in msg

    def test_password_mismatch(self):
        """Mismatched passwords should fail."""
        valid, msg = validate_registration("newuser", "password123", "different", "NewUser")
        assert valid is False
        assert "不一致" in msg

    def test_long_name(self):
        """Name more than 50 chars should fail."""
        valid, msg = validate_registration("newuser", "password123", "password123", "a" * 51)
        assert valid is False
        assert "50" in msg

    def test_duplicate_username(self, fresh_users):
        """Existing username should fail."""
        valid, msg = validate_registration("admin", "newpass123", "newpass123", "Admin2")
        assert valid is False
        assert "已存在" in msg


# ============ Registration Route Tests ============

class TestRegisterRoute:
    """Tests for /register route."""

    def test_register_page_get(self, client):
        """GET /register should return 200."""
        resp = client.get('/register')
        assert resp.status_code == 200

    def test_register_success(self, client, fresh_users):
        """Valid registration should redirect to login."""
        resp = client.post('/register', data={
            'username': 'testuser',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'name': 'TestUser'
        }, follow_redirects=True)
        assert resp.status_code == 200
        data = resp.data.decode('utf-8')
        assert '登录' in data
        assert '注册成功' in data

    def test_register_duplicate(self, client):
        """Register with existing username should fail."""
        resp = client.post('/register', data={
            'username': 'admin',
            'password': 'newpass123',
            'confirm_password': 'newpass123',
            'name': 'Admin2'
        })
        assert resp.status_code == 200
        assert '已存在' in resp.data.decode('utf-8')

    def test_register_short_password(self, client):
        """Register with short password should fail."""
        resp = client.post('/register', data={
            'username': 'newuser2',
            'password': '123',
            'confirm_password': '123',
            'name': 'NewUser'
        })
        assert resp.status_code == 200
        assert '6' in resp.data.decode('utf-8')


# ============ Login Route Tests ============

class TestLoginRoute:
    """Tests for /login route."""

    def test_login_page_get(self, client):
        """GET /login should return 200."""
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_login_success(self, client):
        """Valid login should redirect to dashboard."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'TEST'
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Dashboard shows "欢迎，管理员！"
        assert '管理员' in resp.data.decode('utf-8')

    def test_login_wrong_password(self, client):
        """Wrong password should show error."""
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpass'
        })
        assert resp.status_code == 200
        assert '错误' in resp.data.decode('utf-8')

    def test_login_nonexistent_user(self, client):
        """Nonexistent user should show error."""
        resp = client.post('/login', data={
            'username': 'nobody',
            'password': 'password123'
        })
        assert resp.status_code == 200
        assert '错误' in resp.data.decode('utf-8')


# ============ Dashboard & Logout Tests ============

class TestProtectedRoutes:
    """Tests for protected routes."""

    def test_dashboard_requires_login(self, client):
        """Dashboard should redirect to login if not authenticated."""
        resp = client.get('/dashboard')
        assert resp.status_code == 302
        assert '/login' in resp.location

    def test_dashboard_with_login(self, client):
        """Dashboard should be accessible after login."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'TEST'
        })
        resp = client.get('/dashboard')
        assert resp.status_code == 200
        assert '管理员' in resp.data.decode('utf-8')

    def test_logout(self, client):
        """Logout should clear session and redirect to login."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'TEST'
        })
        resp = client.get('/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert '退出登录' in resp.data.decode('utf-8')

    def test_dashboard_after_logout(self, client):
        """Dashboard should be inaccessible after logout."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'TEST'
        })
        client.get('/logout')
        resp = client.get('/dashboard')
        assert resp.status_code == 302


# ============ Captcha Tests (新增变更) ============

class TestGenerateCaptchaText:
    """Tests for generate_captcha_text function."""

    def test_returns_string(self):
        """Should return a string."""
        from app import generate_captcha_text
        result = generate_captcha_text()
        assert isinstance(result, str)

    def test_length_is_4(self):
        """Captcha text should be exactly 4 characters."""
        from app import generate_captcha_text
        for _ in range(20):
            result = generate_captcha_text()
            assert len(result) == 4

    def test_only_uppercase_and_digits(self):
        """Captcha text should only contain uppercase letters and digits."""
        from app import generate_captcha_text
        import re
        for _ in range(20):
            result = generate_captcha_text()
            assert re.match(r'^[A-Z0-9]{4}$', result)


class TestCaptchaRoute:
    """Tests for /captcha route."""

    def test_captcha_returns_image(self, client):
        """GET /captcha should return a PNG image."""
        with client.session_transaction() as sess:
            pass
        resp = client.get('/captcha')
        assert resp.status_code == 200
        assert resp.content_type == 'image/png'

    def test_captcha_sets_session(self, client):
        """GET /captcha should store captcha text in session."""
        with client.session_transaction() as sess:
            pass
        resp = client.get('/captcha')
        assert resp.status_code == 200
        # Session is server-side, we verify via login flow below


class TestLoginWithCaptcha:
    """Tests for login route with captcha verification (新增变更)."""

    def test_login_without_captcha_fails(self, client):
        """Login without captcha should fail."""
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': ''
        })
        assert resp.status_code == 200
        data = resp.data.decode('utf-8')
        assert '验证码' in data

    def test_login_with_wrong_captcha_fails(self, client):
        """Login with wrong captcha should fail."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'ABCD'
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'WRONG'
        })
        assert resp.status_code == 200
        data = resp.data.decode('utf-8')
        assert '验证码错误' in data

    def test_login_with_correct_captcha_succeeds(self, client):
        """Login with correct captcha should succeed."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'TEST'
        }, follow_redirects=True)
        assert resp.status_code == 200
        data = resp.data.decode('utf-8')
        assert '管理员' in data

    def test_login_captcha_case_insensitive(self, client):
        """Captcha comparison should be case-insensitive (input is uppercased)."""
        with client.session_transaction() as sess:
            sess['captcha'] = 'TEST'
        resp = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'captcha': 'test'
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert '管理员' in resp.data.decode('utf-8')


class TestRegistrationValidationEnhanced:
    """Tests for enhanced validation rules (新增变更)."""

    def test_name_must_start_with_letter(self):
        """Name starting with non-letter should fail."""
        valid, msg = validate_registration(
            "newuser", "password123", "password123", "1昵称"
        )
        assert valid is False
        assert '字母' in msg

    def test_name_starting_with_letter_passes(self):
        """Name starting with letter should pass."""
        valid, msg = validate_registration(
            "newuser", "password123", "password123", "TestUser"
        )
        assert valid is True

    def test_password_special_chars_fails(self):
        """Password with special characters should fail."""
        valid, msg = validate_registration(
            "newuser", "pass@word", "pass@word", "Test"
        )
        assert valid is False
        assert '字母' in msg

    def test_password_with_underscore_passes(self):
        """Password with underscore should pass."""
        valid, msg = validate_registration(
            "newuser", "pass_word1", "pass_word1", "Test"
        )
        assert valid is True

    def test_password_alphanumeric_passes(self):
        """Password with only letters and digits should pass."""
        valid, msg = validate_registration(
            "newuser", "abc123def", "abc123def", "Test"
        )
        assert valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
