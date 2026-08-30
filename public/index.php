<?php
session_start();

require __DIR__ . '/../app/core/Router.php';
require __DIR__ . '/../app/core/Csrf.php';

$router = new Router();

// Auth
$router->get('login',         ['AuthController', 'showLogin']);
$router->post('login',        ['AuthController', 'login']);
$router->get('logout',        ['AuthController', 'logout']);
$router->get('register',      ['AuthController', 'showRegister']);
$router->post('register',     ['AuthController', 'register']);
$router->get('register-done', ['AuthController', 'registerDone']);
$router->get('confirm',       ['AuthController', 'confirm']);
$router->get('forgot',        ['AuthController', 'showForgot']);
$router->post('forgot',       ['AuthController', 'forgot']);
$router->get('reset',         ['AuthController', 'showReset']);
$router->post('reset',        ['AuthController', 'reset']);
$router->get('profile',       ['AuthController', 'showProfile']);
$router->post('profile',      ['AuthController', 'profile']);

// Feed
$router->get('home',          ['FeedController', 'index']);
$router->post('like',         ['FeedController', 'like']);
$router->post('comment',      ['FeedController', 'comment']);

// Editor
$router->get('editor',        ['EditorController', 'show']);
$router->post('capture',      ['EditorController', 'capture']);
$router->post('upload',       ['EditorController', 'upload']);
$router->post('delete-image', ['EditorController', 'delete']);

$page = $_GET['page'] ?? 'home';
$router->dispatch($_SERVER['REQUEST_METHOD'], $page);
