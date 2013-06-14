<?php
   require_once("scripts/thunder.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
      $authorization->Redirect("index.php");
      exit;
   }

   $user = $_GET['uname'];
   $fname = $authorization->SaveUser($user);
   session_start();
   $_SESSION['mode'] = "file";
   $_SESSION['dat_file'] = $fname;
   $authorization->Redirect("admin.php");
?>
