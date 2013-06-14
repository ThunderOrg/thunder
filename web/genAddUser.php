<?php
   require_once("scripts/thunder.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
      $authorization->Redirect("index.php");
      exit;
   }

   $data = $authorization->GenerateAddForm();
   session_start();
   $_SESSION['mode'] = "data";
   $_SESSION['data'] = $data;
   $authorization->Redirect("admin.php");
?>
