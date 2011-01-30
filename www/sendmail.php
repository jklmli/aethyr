<?php
	$email = $_REQUEST['email'];
	$subject = $_REQUEST['subject'];
	$message = $_REQUEST['message'];
	
	if (!isset($_REQUEST['email']))
   		header( "Location: http://www.aethyrjb.com/feedback.html" );
	elseif(empty($message))
		header( "Location: http://www.aethyrjb.com/error.html" );
	else{
		mail( "contact@aethyrjb.com", $subject, $message, "From: $email" );
		header( "Location: http://www.aethyrjb.com/thanks.html" );
	}
?>
