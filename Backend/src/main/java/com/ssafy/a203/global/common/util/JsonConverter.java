package com.ssafy.a203.global.common.util;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.List;

@Converter
public class JsonConverter implements AttributeConverter<List<List<Double>>, String> {

    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(List<List<Double>> attributes) {
        try {
            return mapper.writeValueAsString(attributes);
        } catch (Exception e) {
            throw new IllegalArgumentException("Polygon을 JSON으로 변환하는 데 실패했습니다.", e);
        }
    }

    @Override
    public List<List<Double>> convertToEntityAttribute(String s) {
        try {
            return mapper.readValue(s, new TypeReference<>() {
            });
        } catch (Exception e) {
            throw new IllegalArgumentException("Json 문자열을 Polygon으로 변화하는 데 실패했습니다.", e);
        }
    }
}
