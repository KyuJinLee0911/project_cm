package com.ssafy.a203.global.common.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.security.SecurityScheme.In;
import io.swagger.v3.oas.models.security.SecurityScheme.Type;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    private static final String SCHEMA_NAME = "Authorization";

    @Bean
    public OpenAPI openAPI(){
        Server server = new Server();
        server.setUrl("https://k13a203.p.ssafy.io");
        return new OpenAPI().info(apiInfo()).components(appAuthorization()).addSecurityItem(security());
    }

    private Info apiInfo(){
        return new Info()
                .title("Climb Mate")
                .description("Climbmate REST API")
                .version("v1.0.0");
    }

    private Components appAuthorization(){
        return new Components()
                .addSecuritySchemes(SCHEMA_NAME, new SecurityScheme()
                        .name(SCHEMA_NAME)
                        .type(Type.APIKEY)
                        .in(In.HEADER));

    }

    private SecurityRequirement security(){
        return new SecurityRequirement().addList(SCHEMA_NAME);
    }

}
