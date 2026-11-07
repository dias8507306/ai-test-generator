import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;

public class SimpleWebServer {
    public static void main(String[] args) throws IOException {
        int port = 8080;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        
        server.createContext("/", new Handler("page1.html"));
        server.createContext("/projects", new Handler("page2.html"));
        server.createContext("/contact", new Handler("page3.html"));
        
        server.createContext("/style.css", exchange -> {
            sendFile(exchange, "style.css", "text/css");
        });
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("✅ Сервер запущен: http://localhost:" + port);
    }
    
    static class Handler implements HttpHandler {
        private String fileName;
        
        Handler(String fileName) {
            this.fileName = fileName;
        }
        
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            sendFile(exchange, fileName, "text/html");
        }
    }
    
    static void sendFile(HttpExchange exchange, String fileName, String contentType) throws IOException {
        try {
            String content = new String(Files.readAllBytes(Paths.get(fileName)));
            exchange.getResponseHeaders().set("Content-Type", contentType + "; charset=UTF-8");
            exchange.sendResponseHeaders(200, content.getBytes().length);
            
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(content.getBytes());
            }
        } catch (IOException e) {
            String error = "<h1>Ошибка 404</h1>";
            exchange.sendResponseHeaders(404, error.getBytes().length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(error.getBytes());
            }
        }
    }
}