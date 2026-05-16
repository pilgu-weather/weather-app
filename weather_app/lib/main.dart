import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  final String url = "https://weather-app-1-xy3b.onrender.com";

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text("날씨 코디 앱")),
        body: Center(
          child: ElevatedButton(
            onPressed: () async {
              final Uri uri = Uri.parse(url);
              if (!await launchUrl(uri)) {
                throw 'Could not launch';
              }
            },
            child: Text("앱 열기"),
          ),
        ),
      ),
    );
  }
}