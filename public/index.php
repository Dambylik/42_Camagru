<?php
// Front controller: the single entry point. All URLs are index.php?page=...
session_start();

require __DIR__ . '/../app/core/Router.php';

$router = new Router();

// METHOD + page -> [Controller, method]
$router->get('home',    ['FeedController', 'index']);
$router->get('login',   ['AuthController', 'showLogin']);
$router->post('login',  ['AuthController', 'login']);
$router->get('logout',  ['AuthController', 'logout']);

$page = $_GET['page'] ?? 'home';
$router->dispatch($_SERVER['REQUEST_METHOD'], $page);
