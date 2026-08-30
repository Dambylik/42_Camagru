<?php
require_once __DIR__ . '/../models/User.php';
require_once __DIR__ . '/../core/Mailer.php';

class AuthController
{
    // ── Registration ────────────────────────────────────────────────────────

    public function showRegister(): void
    {
        $error = $_SESSION['reg_error'] ?? null;
        $old   = $_SESSION['reg_old']   ?? [];
        unset($_SESSION['reg_error'], $_SESSION['reg_old']);
        require __DIR__ . '/../views/register.php';
    }

    public function register(): void
    {
        Csrf::verify();
        $username = trim($_POST['username'] ?? '');
        $email    = trim($_POST['email']    ?? '');
        $password =      $_POST['password'] ?? '';

        $error = $this->validateRegistration($username, $email, $password);

        if ($error) {
            $_SESSION['reg_error'] = $error;
            $_SESSION['reg_old']   = ['username' => $username, 'email' => $email];
            header('Location: index.php?page=register');
            exit;
        }

        try {
            $id    = User::create($username, $email, $password);
            $token = User::getVerifyToken($id);
            $url   = rtrim(getenv('APP_URL'), '/') . '/index.php?page=confirm&token=' . $token;
            Mailer::send(
                $email,
                'Confirm your Camagru account',
                "Hi {$username},\n\nClick the link below to confirm your email address:\n{$url}\n\nThe link expires in 24 hours."
            );
        } catch (PDOException $e) {
            // Duplicate entry (race condition after our uniqueness check)
            $_SESSION['reg_error'] = 'Username or email already taken.';
            $_SESSION['reg_old']   = ['username' => $username, 'email' => $email];
            header('Location: index.php?page=register');
            exit;
        }

        $_SESSION['reg_success'] = true;
        header('Location: index.php?page=register-done');
        exit;
    }

    public function confirm(): void
    {
        $token = trim($_GET['token'] ?? '');

        if ($token === '') {
            $message = 'Invalid confirmation link.';
            require __DIR__ . '/../views/error.php';
            return;
        }

        $user = User::findByVerifyToken($token);

        if (!$user) {
            $message = 'This confirmation link is invalid or has expired.';
            require __DIR__ . '/../views/error.php';
            return;
        }

        User::verifyToken($user['id']);
        $_SESSION['confirm_success'] = true;
        header('Location: index.php?page=login');
        exit;
    }

    // ── Login ────────────────────────────────────────────────────────────────

    public function showLogin(): void
    {
        $error   = $_SESSION['login_error']   ?? null;
        $success = $_SESSION['login_success'] ?? $_SESSION['confirm_success'] ?? null;
        if ($success === true) $success = 'Email confirmed! You can now log in.';
        $old     = $_SESSION['login_old']     ?? [];
        unset($_SESSION['login_error'], $_SESSION['login_success'], $_SESSION['confirm_success'], $_SESSION['login_old']);
        require __DIR__ . '/../views/login.php';
    }

    public function login(): void
    {
        Csrf::verify();
        $username = trim($_POST['username'] ?? '');
        $password =      $_POST['password'] ?? '';

        if ($username === '' || $password === '') {
            $this->loginFail('All fields are required.', $username);
        }

        $user = User::findByUsername($username);

        // Same message whether user doesn't exist or password is wrong — no enumeration
        if (!$user || !password_verify($password, $user['password'])) {
            $this->loginFail('Invalid username or password.', $username);
        }

        if (!$user['is_verified']) {
            $this->loginFail('Please confirm your email address before logging in.', $username);
        }

        // Prevent session fixation: regenerate ID on privilege change
        session_regenerate_id(true);

        $_SESSION['user_id']   = $user['id'];
        $_SESSION['username']  = $user['username'];

        header('Location: index.php?page=home');
        exit;
    }

    private function loginFail(string $message, string $username): never
    {
        $_SESSION['login_error'] = $message;
        $_SESSION['login_old']   = ['username' => $username];
        header('Location: index.php?page=login');
        exit;
    }

    public function logout(): void
    {
        session_destroy();
        header('Location: index.php?page=login');
        exit;
    }

    // ── Password reset ───────────────────────────────────────────────────────

    public function showForgot(): void
    {
        $success = $_SESSION['forgot_success'] ?? null;
        $error   = $_SESSION['forgot_error']   ?? null;
        unset($_SESSION['forgot_success'], $_SESSION['forgot_error']);
        require __DIR__ . '/../views/forgot.php';
    }

    public function forgot(): void
    {
        Csrf::verify();
        $email = trim($_POST['email'] ?? '');

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $_SESSION['forgot_error'] = 'Invalid email address.';
            header('Location: index.php?page=forgot');
            exit;
        }

        // Always show the same message — don't reveal whether the email exists
        $user = User::findByEmail($email);
        if ($user) {
            $token = User::setResetToken($user['id']);
            $url   = rtrim(getenv('APP_URL'), '/') . '/index.php?page=reset&token=' . $token;
            Mailer::send(
                $email,
                'Reset your Camagru password',
                "Hi {$user['username']},\n\nClick the link below to set a new password:\n{$url}\n\nThe link expires in 1 hour. If you did not request this, ignore this email."
            );
        }

        $_SESSION['forgot_success'] = 'If that email is registered you will receive a reset link shortly.';
        header('Location: index.php?page=forgot');
        exit;
    }

    public function showReset(): void
    {
        $token = trim($_GET['token'] ?? '');
        $error = $_SESSION['reset_error'] ?? null;
        unset($_SESSION['reset_error']);

        if (!$token || !User::findByResetToken($token)) {
            $message = 'This reset link is invalid or has expired.';
            require __DIR__ . '/../views/error.php';
            return;
        }

        require __DIR__ . '/../views/reset.php';
    }

    public function reset(): void
    {
        Csrf::verify();
        $token    = trim($_POST['token']    ?? '');
        $password =      $_POST['password'] ?? '';

        $user = $token ? User::findByResetToken($token) : false;

        if (!$user) {
            $message = 'This reset link is invalid or has expired.';
            require __DIR__ . '/../views/error.php';
            return;
        }

        if (!$this->passwordStrong($password)) {
            $_SESSION['reset_error'] = 'Password must be at least 8 characters and include an uppercase letter, a digit, and a special character.';
            header('Location: index.php?page=reset&token=' . urlencode($token));
            exit;
        }

        User::updatePassword($user['id'], $password);

        $_SESSION['login_success'] = 'Password updated! You can now log in.';
        header('Location: index.php?page=login');
        exit;
    }

    // ── Profile ──────────────────────────────────────────────────────────────

    public function showProfile(): void
    {
        $this->requireLogin();
        $user    = User::findById($_SESSION['user_id']);
        $success = $_SESSION['profile_success'] ?? null;
        $error   = $_SESSION['profile_error']   ?? null;
        unset($_SESSION['profile_success'], $_SESSION['profile_error']);
        require __DIR__ . '/../views/profile.php';
    }

    public function profile(): void
    {
        $this->requireLogin();
        Csrf::verify();
        $id     = $_SESSION['user_id'];
        $action = $_POST['action'] ?? '';

        switch ($action) {
            case 'username':
                $username = trim($_POST['username'] ?? '');
                if (!preg_match('/^\w{3,30}$/', $username)) {
                    $_SESSION['profile_error'] = 'Username must be 3–30 characters (letters, digits, underscore).';
                    break;
                }
                $existing = User::findByUsername($username);
                if ($existing && $existing['id'] !== $id) {
                    $_SESSION['profile_error'] = 'Username already taken.';
                    break;
                }
                User::updateUsername($id, $username);
                $_SESSION['username']        = $username;  // keep session in sync
                $_SESSION['profile_success'] = 'Username updated.';
                break;

            case 'email':
                $email = trim($_POST['email'] ?? '');
                if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
                    $_SESSION['profile_error'] = 'Invalid email address.';
                    break;
                }
                $existing = User::findByEmail($email);
                if ($existing && $existing['id'] !== $id) {
                    $_SESSION['profile_error'] = 'Email already registered.';
                    break;
                }
                User::updateEmail($id, $email);
                $_SESSION['profile_success'] = 'Email updated.';
                break;

            case 'password':
                $current = $_POST['current_password'] ?? '';
                $new     = $_POST['new_password']     ?? '';
                $user    = User::findById($id);
                if (!password_verify($current, $user['password'])) {
                    $_SESSION['profile_error'] = 'Current password is incorrect.';
                    break;
                }
                if (!$this->passwordStrong($new)) {
                    $_SESSION['profile_error'] = 'New password must be at least 8 characters and include an uppercase letter, a digit, and a special character.';
                    break;
                }
                User::updatePassword($id, $new);
                $_SESSION['profile_success'] = 'Password updated.';
                break;

            case 'notify':
                $val = isset($_POST['notify_on_comment']) ? 1 : 0;
                User::updateNotify($id, $val);
                $_SESSION['profile_success'] = 'Notification preference saved.';
                break;

            default:
                $_SESSION['profile_error'] = 'Invalid action.';
        }

        header('Location: index.php?page=profile');
        exit;
    }

    private function requireLogin(): void
    {
        if (empty($_SESSION['user_id'])) {
            header('Location: index.php?page=login');
            exit;
        }
    }

    // ── Registration done ────────────────────────────────────────────────────

    public function registerDone(): void
    {
        if (empty($_SESSION['reg_success'])) {
            header('Location: index.php?page=register');
            exit;
        }
        unset($_SESSION['reg_success']);
        $pageTitle = 'Check your email — Camagru';
        require __DIR__ . '/../views/register_done.php';
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private function validateRegistration(string $username, string $email, string $password): ?string
    {
        if ($username === '' || $email === '' || $password === '') {
            return 'All fields are required.';
        }
        if (!preg_match('/^\w{3,30}$/', $username)) {
            return 'Username must be 3–30 characters (letters, digits, underscore).';
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return 'Invalid email address.';
        }
        if (!$this->passwordStrong($password)) {
            return 'Password must be at least 8 characters and include an uppercase letter, a digit, and a special character.';
        }
        if (User::findByEmail($email)) {
            return 'Email already registered.';
        }
        if (User::findByUsername($username)) {
            return 'Username already taken.';
        }
        return null;
    }

    private function passwordStrong(string $p): bool
    {
        return strlen($p) >= 8
            && preg_match('/[A-Z]/', $p)
            && preg_match('/[0-9]/', $p)
            && preg_match('/[\W_]/', $p);   // special char
    }
}
