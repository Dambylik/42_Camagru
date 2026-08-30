<?php
class Mailer
{
    public static function send(string $to, string $subject, string $body): void
    {
        $from    = getenv('MAIL_FROM') ?: 'noreply@camagru.local';
        $headers = "From: {$from}\r\nContent-Type: text/plain; charset=UTF-8";

        if (!mail($to, $subject, $body, $headers)) {
            error_log("Mailer: failed to send to {$to}");
        }
    }
}
