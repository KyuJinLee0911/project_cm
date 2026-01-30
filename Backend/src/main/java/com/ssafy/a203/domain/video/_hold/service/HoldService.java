package com.ssafy.a203.domain.video._hold.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.a203.domain.video._hold.dto.request.HoldDetectionRequest;
import com.ssafy.a203.domain.video._hold.dto.response.HoldInfoResponse;
import com.ssafy.a203.domain.video._hold.dto.response.HoldListResponse;
import com.ssafy.a203.domain.video._hold.dto.response.SessionOpenResponse;
import com.ssafy.a203.domain.video._hold.entity.Hold;
import com.ssafy.a203.domain.video._hold.exception.FileTransferException;
import com.ssafy.a203.domain.video._hold.exception.HoldNotBelongsException;
import com.ssafy.a203.domain.video._hold.exception.InvalidSessionException;
import com.ssafy.a203.domain.video.entity.Video;
import jakarta.annotation.PostConstruct;
import java.io.File;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Service
@RequiredArgsConstructor
public class HoldService {

    private final HoldReader holdReader;
    private final HoldStore holdStore;
    //    private final WebClient aiWebClient;
    private final RestClient restClient;
    @Autowired
    private ApplicationContext context;

    @PostConstruct
    public void checkBeans() {
        System.out.println(
                ">>> Beans of type WebClient: " + context.getBeansOfType(RestClient.class)
                        .keySet());
    }

    @PostConstruct
    public void init() {
        System.out.println(">>> HoldService restClient = " + restClient);
        System.out.println(">>> HoldService restClient class = " + restClient.getClass());
    }

    // 홀드 인식 요청 -> 세션 생성 -> 홀드 초기 정보 등록 -> 홀드 인식 요청 -> 리턴값을 토대로 폴리곤 저장 및 프론트로 응답 보냄 -> 반복
    // 홀드 인식 세션 생성
    @Transactional
    public SessionOpenResponse openSession(Video video, MultipartFile file) {

        try {
            File temp = File.createTempFile("upload-", file.getOriginalFilename());
            file.transferTo(temp);
            FileSystemResource fsr = new FileSystemResource(temp);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("image", fsr);

            JsonNode response = restClient.post()
                    .uri("/ai/v1/hold/sessions")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(body)
                    .retrieve()
                    .body(JsonNode.class);

            String sessionId = response.get("session_id").asText();
            temp.delete();
            video.updateSessionId(sessionId);
            return SessionOpenResponse.of(sessionId);
        } catch (Exception e) {
            log.error(e.getMessage());
            throw new FileTransferException();
        }
    }

    // 세션 상태 확인
    public boolean isSessionValid(String sessionId) {
        try {
            JsonNode response = restClient.get()
                    .uri("/ai/v1/hold/sessions/{sessionId}", sessionId)
                    .retrieve()
                    .body(JsonNode.class);

            return response.get("status").asText().equals("active");
        } catch (InvalidSessionException e) {
            return false;
        }
    }

    // 홀드 인식
    @Transactional
    public HoldInfoResponse detectHold(HoldDetectionRequest request, Video video) {

        Hold hold = Hold.from(request, video);

        JsonNode response = restClient.post()
                .uri("/ai/v1/hold/sessions/{session_id}/holds:detect"
                        , video.getSessionId())
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(JsonNode.class);

        ObjectMapper mapper = new ObjectMapper();

        // "points"를 List<List<Double>>로 변환
        List<List<Double>> polygon = mapper.convertValue(
                response.get("polygon"),
                new TypeReference<>() {
                }
        );

        List<Double> bbox = mapper.convertValue(
                response.get("bbox"),
                new TypeReference<>() {
                }
        );

        hold.updatePolygonAndBox(polygon, bbox);

        return HoldInfoResponse.from(holdStore.save(hold));
    }

    // 전체 홀드 정보 조회
    @Transactional(readOnly = true)
    public HoldListResponse getHoldInformations(Long videoId) {
        List<Hold> holds = holdReader.getHoldsByVideoId(videoId);

        List<HoldInfoResponse> holdInfoList = holds.stream().map(HoldInfoResponse::from).toList();

        return HoldListResponse.of(videoId, holdInfoList);
    }

    @Transactional
    public void removeHold(Long videoId, Long holdId) {
        Hold hold = holdReader.getHold(holdId);
        if (!hold.getVideo().getId().equals(videoId)) {
            throw new HoldNotBelongsException();
        }
        hold.deleteHold();
    }

    public List<Hold> getHoldList(Long videoId) {
        return holdReader.getHoldsByVideoId(videoId);
    }

    // 세션 종료
    public void closeSession(String sessionId) {
        JsonNode response = restClient.post()
                .uri("/ai/v1/hold/sessions/{session_id}:close", sessionId)
                .contentType(MediaType.APPLICATION_JSON)
                .retrieve()
                .body(JsonNode.class);
    }
}
