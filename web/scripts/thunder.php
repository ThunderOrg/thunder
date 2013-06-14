<?php
   require_once("authorization.php");
   require_once("communication.php");
   $authorization = new Authorization();
   $authorization->InitDB('localhost','root','thunder','thunder','user');
   $comm = new Communication();
?>
