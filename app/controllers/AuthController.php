<?php
// ponytail: stubs — wire up real auth (validate, DB, sessions) when building login.
class AuthController
{
    public function showLogin(): void
    {
        echo '<form method="post" action="index.php?page=login">'
           . '<input name="username" placeholder="username">'
           . '<input name="password" type="password" placeholder="password">'
           . '<button>Log in</button></form>';
    }

    public function login(): void
    {
        // TODO: validate $_POST, check DB, set $_SESSION, then redirect.
        header('Location: index.php?page=home');
    }

    public function logout(): void
    {
        session_destroy();
        header('Location: index.php?page=login');
    }
}
