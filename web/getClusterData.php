<?php
   require_once("scripts/CARECloud.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
      $authorization->Redirect("index.php");
      exit;
   }

   $cluster = $_GET['cname'];
   $fname = $comm->SaveStats($cluster);
   session_start();
   $_SESSION['dat_file'] = $fname;
   $authorization->Redirect("admin.php");

?>
