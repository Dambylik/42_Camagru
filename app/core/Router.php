<?php
// Small router: maps "METHOD page" -> [Controller, method].
// "page" comes from the ?page= query string, e.g. index.php?page=login
class Router
{
    private array $routes = [];

    public function get(string $page, array $handler): void
    {
        $this->routes['GET ' . $page] = $handler;
    }

    public function post(string $page, array $handler): void
    {
        $this->routes['POST ' . $page] = $handler;
    }

    public function dispatch(string $method, string $page): void
    {
        $key = $method . ' ' . $page;

        if (!isset($this->routes[$key])) {
            http_response_code(404);
            require __DIR__ . '/../views/404.php';
            return;
        }

        [$class, $action] = $this->routes[$key];
        require __DIR__ . '/../controllers/' . $class . '.php';
        (new $class())->$action();
    }
}
