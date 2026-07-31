<?php

/*

GlkOte transcript recording server
==================================

Copyright (c) 2022 Dannii Willis
MIT licenced
https://github.com/curiousdannii/asyncglk

*/

function show_error($code, $message) {
    http_response_code($code);
    echo $message;
    die();
}

// Allow all requests
header("Access-Control-Allow-Origin: *");

$method = $_SERVER['REQUEST_METHOD'];
if ($method !== 'POST' && $method !== 'OPTIONS') {
    show_error(405, 'This transcript server only accepts POST requests');
}

// Support CORS preflight requests
if ($method === 'OPTIONS') {
    header('Access-Control-Allow-Methods: OPTIONS, POST');
    header('Access-Control-Max-Age: 86400');
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'])) {
        header("Access-Control-Allow-Headers: {$_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']}");
    }
    exit(0);
}

// Options
$path = getcwd();
$filter_labels = false;
$allowed_labels = [];

// Read the config file if it exists
$config_path = "{$path}/transcript-server-config.json";
if (file_exists($config_path)) {
    $data = file_get_contents($config_path);
    $json = json_decode($data);
    if (isset($json->path)) {
        $path = $json->path;
    }
    if (isset($json->labels)) {
        $filter_labels = true;
        $allowed_labels = $json->labels;
    }
}

// Read the POST body
$body = file_get_contents('php://input');
$payload = json_decode($body);
if (!$payload) {
    show_error(400, 'POST body is not valid JSON');
}

if (!isset($payload->format) || $payload->format !== 'simple') {
    show_error(400, 'Only the Simple format is supported');
}

// Check for the session ID
if (!isset($payload->sessionId)) {
    show_error(400, 'Missing session ID');
}
if (!is_string($payload->sessionId)) {
    show_error(400, 'Invalid session ID');
}
$session = $payload->sessionId;

// Read and check the label
$label = '';
if (isset($payload->label) && is_string($payload->label)) {
    $label = $payload->label;
}
if ($filter_labels) {
    if (!in_array($label, $allowed_labels)) {
        show_error(400, 'Story label not in the allowed list');
    }
}

// Check if we need to create the destination folder
$label_path = "{$path}/{$label}";
if (!file_exists($label_path)) {
    mkdir($label_path, 0777, true);
}

// We currently only use the output
/*$input = '';
if (isset($payload->input) && is_string($payload->input)) {
    $input = $payload->input;
}*/
$output = '';
if (isset($payload->output) && is_string($payload->output)) {
    $output = $payload->output;
}

// Create/append the transcript file
$session_path = "{$label_path}/{$session}.txt";
file_put_contents($session_path, $output, FILE_APPEND | LOCK_EX);

echo 'Transcript update successfully received';